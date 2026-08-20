import { Injectable, OnDestroy } from '@angular/core';
import {
  BehaviorSubject,
  Observable,
  Subject,
  takeUntil
} from 'rxjs';

import { Esp32WebsocketService } from './esp32-websocket.service';

@Injectable({
  providedIn: 'root'
})
export class EcgProcessingService implements OnDestroy {

  // ============================================================
  // CONFIGURATION
  // ============================================================

  private readonly SAMPLE_RATE = 250;

  /**
   * Number of ECG samples displayed.
   *
   * 750 samples / 250 Hz = 3 seconds
   */
  private readonly DISPLAY_BUFFER_SIZE = 750;

  /**
   * Number of ECG samples used for HR calculation.
   *
   * 2000 / 250 Hz = 8 seconds
   */
  private readonly ANALYSIS_BUFFER_SIZE = 2000;

  /**
   * Minimum distance between two R peaks.
   *
   * 0.33 second = approximately 181 BPM maximum.
   */
  private readonly MIN_RR_SAMPLES = Math.floor(
    0.33 * this.SAMPLE_RATE
  );

  // ============================================================
  // DESTROY
  // ============================================================

  private readonly destroy$ = new Subject<void>();

  // ============================================================
  // RAW ECG
  // ============================================================

  private readonly rawEcgSubject =
    new BehaviorSubject<number[]>([]);

  readonly rawEcg$: Observable<number[]> =
    this.rawEcgSubject.asObservable();

  // ============================================================
  // FILTERED ECG
  // ============================================================

  private readonly filteredEcgSubject =
    new BehaviorSubject<number[]>([]);

  readonly filteredEcg$: Observable<number[]> =
    this.filteredEcgSubject.asObservable();

  // ============================================================
  // R PEAKS
  // ============================================================

  private readonly rPeaksSubject =
    new BehaviorSubject<number[]>([]);

  readonly rPeaks$: Observable<number[]> =
    this.rPeaksSubject.asObservable();

  // ============================================================
  // CALCULATED HEART RATE
  // ============================================================

  private readonly heartRateSubject =
    new BehaviorSubject<number | null>(null);

  readonly heartRate$: Observable<number | null> =
    this.heartRateSubject.asObservable();

  // ============================================================
  // FILTERING STATE
  // ============================================================

  private filterInitialized = false;

  private filterPreviousInput = 0;

  private filterPreviousOutput = 0;

  // ============================================================
  // INTERNAL BUFFERS
  // ============================================================

  private rawBuffer: number[] = [];

  private filteredBuffer: number[] = [];

  private analysisBuffer: number[] = [];

  // ============================================================
  // CONSTRUCTOR
  // ============================================================

  constructor(
    private readonly esp32Service: Esp32WebsocketService
  ) {

    this.subscribeToEcg();
  }

  // ============================================================
  // SUBSCRIBE TO ESP32 ECG STREAM
  // ============================================================

  private subscribeToEcg(): void {

    this.esp32Service.ecg$
      .pipe(
        takeUntil(this.destroy$)
      )
      .subscribe({
        next: (samples) => {

          this.processSamples(samples);
        },

        error: (error) => {

          console.error(
            '[ECG] ECG stream error:',
            error
          );
        }
      });
  }

  // ============================================================
  // PROCESS ECG CHUNK
  // ============================================================

  private processSamples(
    samples: number[]
  ): void {

    if (!samples || samples.length === 0) {

      return;
    }

    // ----------------------------------------------------------
    // 1. Store raw ECG
    // ----------------------------------------------------------

    this.rawBuffer.push(...samples);

    this.limitBuffer(
      this.rawBuffer,
      this.DISPLAY_BUFFER_SIZE
    );

    this.rawEcgSubject.next(
      [...this.rawBuffer]
    );

    // ----------------------------------------------------------
    // 2. Filter ECG
    // ----------------------------------------------------------

    const filteredSamples =
      this.filterSamples(samples);

    // ----------------------------------------------------------
    // 3. Store filtered ECG
    // ----------------------------------------------------------

    this.filteredBuffer.push(
      ...filteredSamples
    );

    this.limitBuffer(
      this.filteredBuffer,
      this.DISPLAY_BUFFER_SIZE
    );

    this.filteredEcgSubject.next(
      [...this.filteredBuffer]
    );

    // ----------------------------------------------------------
    // 4. Store analysis data
    // ----------------------------------------------------------

    this.analysisBuffer.push(
      ...filteredSamples
    );

    this.limitBuffer(
      this.analysisBuffer,
      this.ANALYSIS_BUFFER_SIZE
    );

    // ----------------------------------------------------------
    // 5. Detect R peaks
    // ----------------------------------------------------------

    this.detectRPeaks();
  }

  // ============================================================
  // ECG FILTER
  // ============================================================

  /**
   * Lightweight streaming ECG filter.
   *
   * This is intentionally implemented without external DSP
   * dependencies so Angular can process the signal locally.
   *
   * Current filter:
   *
   *      ECG
   *       ↓
   *   High-pass component
   *       ↓
   *   Low-pass component
   *       ↓
   *   Filtered ECG
   *
   * Later we can replace this with a more precise digital
   * Butterworth + 50 Hz notch implementation.
   */
  private filterSamples(
    samples: number[]
  ): number[] {

    const result: number[] = [];

    if (samples.length === 0) {

      return result;
    }

    /**
     * Simple first-order low-pass filter.
     *
     * Cutoff is approximately 40 Hz.
     */
    const lowPassAlpha = 0.60;

    /**
     * Simple high-pass component.
     *
     * This removes slow baseline drift.
     */
    const highPassAlpha = 0.995;

    for (const sample of samples) {

      // --------------------------------------------------------
      // Initialization
      // --------------------------------------------------------

      if (!this.filterInitialized) {

        this.filterPreviousInput = sample;

        this.filterPreviousOutput = 0;

        this.filterInitialized = true;
      }

      // --------------------------------------------------------
      // High-pass
      // --------------------------------------------------------

      const highPass =
        highPassAlpha *
        (
          this.filterPreviousOutput +
          sample -
          this.filterPreviousInput
        );

      this.filterPreviousInput = sample;

      // --------------------------------------------------------
      // Low-pass
      // --------------------------------------------------------

      const lowPass =
        lowPassAlpha * this.filterPreviousOutput +
        (1 - lowPassAlpha) * highPass;

      this.filterPreviousOutput = lowPass;

      result.push(lowPass);
    }

    return result;
  }

  // ============================================================
  // R PEAK DETECTION
  // ============================================================

  private detectRPeaks(): void {

    const signal = this.analysisBuffer;

    if (signal.length < this.SAMPLE_RATE * 3) {

      return;
    }

    // ----------------------------------------------------------
    // Calculate mean
    // ----------------------------------------------------------

    const mean =
      signal.reduce(
        (sum, value) => sum + value,
        0
      ) / signal.length;

    // ----------------------------------------------------------
    // Calculate standard deviation
    // ----------------------------------------------------------

    const variance =
      signal.reduce(
        (sum, value) =>
          sum + Math.pow(value - mean, 2),
        0
      ) / signal.length;

    const std = Math.sqrt(variance);

    if (std < 0.000001) {

      return;
    }

    // ----------------------------------------------------------
    // Dynamic threshold
    // ----------------------------------------------------------

    const threshold =
      mean + 0.5 * std;

    // ----------------------------------------------------------
    // Detect peaks
    // ----------------------------------------------------------

    const peaks: number[] = [];

    for (
      let i = 1;
      i < signal.length - 1;
      i++
    ) {

      const current = signal[i];

      const previous = signal[i - 1];

      const next = signal[i + 1];

      // --------------------------------------------------------
      // Local maximum
      // --------------------------------------------------------

      if (
        current > previous &&
        current >= next &&
        current > threshold
      ) {

        // ------------------------------------------------------
        // Enforce minimum distance between R peaks
        // ------------------------------------------------------

        const lastPeak =
          peaks.length > 0
            ? peaks[peaks.length - 1]
            : -Infinity;

        if (
          i - lastPeak >=
          this.MIN_RR_SAMPLES
        ) {

          peaks.push(i);
        }
      }
    }

    // ----------------------------------------------------------
    // Convert analysis indexes to display indexes
    // ----------------------------------------------------------

    const displayOffset =
      Math.max(
        0,
        this.filteredBuffer.length -
        signal.length
      );

    const displayPeaks =
      peaks
        .map(index =>
          index + displayOffset
        )
        .filter(index =>
          index >= 0 &&
          index < this.filteredBuffer.length
        );

    this.rPeaksSubject.next(
      displayPeaks
    );

    // ----------------------------------------------------------
    // Calculate HR
    // ----------------------------------------------------------

    this.calculateHeartRate(peaks);
  }

  // ============================================================
  // HEART RATE
  // ============================================================

  private calculateHeartRate(
    peaks: number[]
  ): void {

    if (peaks.length < 3) {

      return;
    }

    const rrIntervals: number[] = [];

    // ----------------------------------------------------------
    // Calculate RR intervals
    // ----------------------------------------------------------

    for (
      let i = 1;
      i < peaks.length;
      i++
    ) {

      const rr =
        (
          peaks[i] -
          peaks[i - 1]
        ) / this.SAMPLE_RATE;

      // --------------------------------------------------------
      // Accept RR between 0.33 and 1.5 sec
      //
      // approximately 40–180 BPM
      // --------------------------------------------------------

      if (
        rr > 0.33 &&
        rr < 1.5
      ) {

        rrIntervals.push(rr);
      }
    }

    if (rrIntervals.length < 2) {

      return;
    }

    // ----------------------------------------------------------
    // Median RR
    // ----------------------------------------------------------

    const sorted =
      [...rrIntervals].sort(
        (a, b) => a - b
      );

    const middle =
      Math.floor(sorted.length / 2);

    const medianRR =
      sorted.length % 2 === 0
        ? (
            sorted[middle - 1] +
            sorted[middle]
          ) / 2
        : sorted[middle];

    // ----------------------------------------------------------
    // HR = 60 / RR
    // ----------------------------------------------------------

    const heartRate =
      60 / medianRR;

    this.heartRateSubject.next(
      Math.round(heartRate * 10) / 10
    );
  }

  // ============================================================
  // BUFFER LIMIT
  // ============================================================

  private limitBuffer(
    buffer: number[],
    maxSize: number
  ): void {

    if (buffer.length <= maxSize) {

      return;
    }

    const removeCount =
      buffer.length - maxSize;

    buffer.splice(
      0,
      removeCount
    );
  }

  // ============================================================
  // RESET
  // ============================================================

  reset(): void {

    this.rawBuffer = [];

    this.filteredBuffer = [];

    this.analysisBuffer = [];

    this.filterInitialized = false;

    this.filterPreviousInput = 0;

    this.filterPreviousOutput = 0;

    this.rawEcgSubject.next([]);

    this.filteredEcgSubject.next([]);

    this.rPeaksSubject.next([]);

    this.heartRateSubject.next(null);
  }

  // ============================================================
  // GET CURRENT VALUES
  // ============================================================

  getCurrentRawECG(): number[] {

    return [...this.rawBuffer];
  }

  getCurrentFilteredECG(): number[] {

    return [...this.filteredBuffer];
  }

  getCurrentRPeaks(): number[] {

    return this.rPeaksSubject.value;
  }

  getCurrentHeartRate(): number | null {

    return this.heartRateSubject.value;
  }

  // ============================================================
  // CLEANUP
  // ============================================================

  ngOnDestroy(): void {

    this.destroy$.next();

    this.destroy$.complete();

    this.rawEcgSubject.complete();

    this.filteredEcgSubject.complete();

    this.rPeaksSubject.complete();

    this.heartRateSubject.complete();
  }
}