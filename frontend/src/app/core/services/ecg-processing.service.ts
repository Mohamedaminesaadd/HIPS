import { Injectable, OnDestroy, inject } from '@angular/core';
import {
  BehaviorSubject,
  finalize,
  Observable,
  Subject,
  takeUntil
} from 'rxjs';

import { Esp32WebsocketService } from './esp32-websocket.service';
import { EcgApiService } from './ecg-api.service';
import { WearableDataService } from './wearable-data.service';
import { ECG_TRANSPORT_SUBJECT_ID } from '../config/api.config';
import { EcgAnalysisRequest } from '../models/ecg-analysis.model';

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
   * 1250 samples / 250 Hz = 5 seconds
   */
  private readonly DISPLAY_BUFFER_SIZE = 1250;

  /**
   * Number of ECG samples used for HR calculation.
   *
   * 2000 / 250 Hz = 8 seconds
   */
  private readonly ANALYSIS_BUFFER_SIZE = 2000;

  /** Raw 30-second window used only for backend Model A transport. */
  private readonly BACKEND_WINDOW_SIZE =
    this.SAMPLE_RATE * 30;

  /** Keep 20 seconds after each upload; the next window starts 10 seconds later. */
  private readonly BACKEND_WINDOW_STRIDE =
    this.SAMPLE_RATE * 10;

  /** Bounds memory if the API is slow or unavailable. */
  private readonly BACKEND_MAX_BUFFER_SIZE =
    this.BACKEND_WINDOW_SIZE + this.BACKEND_WINDOW_STRIDE;

  private readonly MINIMUM_UPLOAD_QUALITY = 50;

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

  /** This deliberately remains separate from the display and HR buffers. */
  private backendTransportBuffer: number[] = [];

  private backendRequestInFlight = false;

  private destroyed = false;

  private readonly subjectId = inject(ECG_TRANSPORT_SUBJECT_ID);

  // ============================================================
  // CONSTRUCTOR
  // ============================================================

  constructor(
    private readonly esp32Service: Esp32WebsocketService,
    private readonly ecgApiService: EcgApiService,
    private readonly wearableDataService: WearableDataService,
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

    const validSamples = samples?.filter(Number.isFinite) ?? [];

    if (validSamples.length === 0) {

      console.warn('[ECG] Ignoring an empty or invalid ECG chunk.');

      return;
    }

    // Keep raw data for the backend separately; local UI and HR processing
    // remain on their existing short, lightweight buffers.
    this.collectBackendWindow(validSamples);

    // ----------------------------------------------------------
    // 1. Store raw ECG
    // ----------------------------------------------------------

    this.rawBuffer.push(...validSamples);

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
      this.filterSamples(validSamples);

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
  // BACKEND ECG TRANSPORT
  // ============================================================

  private collectBackendWindow(samples: number[]): void {

    this.backendTransportBuffer.push(...samples);

    this.limitBuffer(
      this.backendTransportBuffer,
      this.BACKEND_MAX_BUFFER_SIZE,
    );

    this.trySendBackendWindow();
  }

  private trySendBackendWindow(): void {

    if (
      this.destroyed ||
      this.backendRequestInFlight ||
      this.backendTransportBuffer.length < this.BACKEND_WINDOW_SIZE
    ) {

      return;
    }

    const ecgMetadata = this.wearableDataService.getCurrentECGData();

    if (ecgMetadata?.lead_off) {
      console.warn('[ECG] Backend upload skipped: ECG lead is disconnected.');
      this.advanceBackendWindow();
      return;
    }

    if (this.hasPoorSignal(ecgMetadata?.signal_quality ?? null)) {
      console.warn('[ECG] Backend upload skipped: ECG signal quality is poor.');
      this.advanceBackendWindow();
      return;
    }

    const payload = this.createBackendPayload(
      this.backendTransportBuffer.slice(0, this.BACKEND_WINDOW_SIZE),
    );

    this.advanceBackendWindow();
    this.backendRequestInFlight = true;

    this.ecgApiService.analyzeEcg(payload)
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => {
          this.backendRequestInFlight = false;
          this.trySendBackendWindow();
        }),
      )
      .subscribe({
        next: (response) => {
          console.info(
            `[ECG] Backend accepted ${response.ecg_samples} raw samples ` +
            `for ${response.subject_id}.`,
          );
        },
        error: (error) => {
          // Keep the real-time UI independent from API availability.
          console.error('[ECG] Backend analysis request failed:', error);
        },
      });
  }

  private createBackendPayload(samples: number[]): EcgAnalysisRequest {

    const packet = this.wearableDataService.getCurrentPacket();
    const ecgMetadata = this.wearableDataService.getCurrentECGData();

    return {
      subject_id: this.subjectId,
      timestamp: packet?.timestamp_ms ?? Date.now(),
      ecg: {
        fs: this.SAMPLE_RATE,
        samples,
      },
      vitals: {
        hr: this.heartRateSubject.value ?? this.wearableDataService.getCurrentHeartRate(),
        spo2: this.wearableDataService.getCurrentSpO2(),
        temperature: this.wearableDataService.getCurrentTemperature(),
      },
      quality: {
        ecg_quality: ecgMetadata?.signal_quality ?? null,
        noise: ecgMetadata?.noise_level ?? null,
        lead_off: ecgMetadata?.lead_off ?? false,
      },
    };
  }

  private advanceBackendWindow(): void {

    this.backendTransportBuffer.splice(0, this.BACKEND_WINDOW_STRIDE);
  }

  private hasPoorSignal(quality: number | null): boolean {

    if (quality === null || !Number.isFinite(quality)) {
      return false;
    }

    const percent = quality <= 1 ? quality * 100 : quality;

    return percent < this.MINIMUM_UPLOAD_QUALITY;
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

    this.backendTransportBuffer = [];

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

    this.destroyed = true;

    this.destroy$.next();

    this.destroy$.complete();

    this.rawEcgSubject.complete();

    this.filteredEcgSubject.complete();

    this.rPeaksSubject.complete();

    this.heartRateSubject.complete();
  }
}
