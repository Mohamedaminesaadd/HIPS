import { Injectable, OnDestroy } from '@angular/core';
import {
  BehaviorSubject,
  Observable,
  Subject,
  takeUntil
} from 'rxjs';

import { Esp32WebsocketService } from './esp32-websocket.service';

import {
  WearablePacket,
  VitalsData,
  ECGData,
  PPGData,
  IMUData,
  BatteryData
} from '../models/wearable-data.model';

@Injectable({
  providedIn: 'root'
})
export class WearableDataService implements OnDestroy {

  // ============================================================
  // DESTROY
  // ============================================================

  private readonly destroy$ = new Subject<void>();

  // ============================================================
  // LATEST COMPLETE PACKET
  // ============================================================

  private readonly packetSubject =
    new BehaviorSubject<WearablePacket | null>(null);

  readonly packet$: Observable<WearablePacket | null> =
    this.packetSubject.asObservable();

  // ============================================================
  // VITALS
  // ============================================================

  private readonly vitalsSubject =
    new BehaviorSubject<VitalsData | null>(null);

  readonly vitals$: Observable<VitalsData | null> =
    this.vitalsSubject.asObservable();

  // ============================================================
  // HEART RATE
  // ============================================================

  private readonly heartRateSubject =
    new BehaviorSubject<number | null>(null);

  readonly heartRate$: Observable<number | null> =
    this.heartRateSubject.asObservable();

  // ============================================================
  // SPO2
  // ============================================================

  private readonly spo2Subject =
    new BehaviorSubject<number | null>(null);

  readonly spo2$: Observable<number | null> =
    this.spo2Subject.asObservable();

  // ============================================================
  // TEMPERATURE
  // ============================================================

  private readonly temperatureSubject =
    new BehaviorSubject<number | null>(null);

  readonly temperature$: Observable<number | null> =
    this.temperatureSubject.asObservable();

  // ============================================================
  // ECG INFORMATION
  // ============================================================

  private readonly ecgSubject =
    new BehaviorSubject<ECGData | null>(null);

  readonly ecgData$: Observable<ECGData | null> =
    this.ecgSubject.asObservable();

  // ============================================================
  // SIGNAL QUALITY
  // ============================================================

  private readonly signalQualitySubject =
    new BehaviorSubject<number | null>(null);

  readonly signalQuality$: Observable<number | null> =
    this.signalQualitySubject.asObservable();

  // ============================================================
  // NOISE
  // ============================================================

  private readonly noiseLevelSubject =
    new BehaviorSubject<number | null>(null);

  readonly noiseLevel$: Observable<number | null> =
    this.noiseLevelSubject.asObservable();

  // ============================================================
  // LEAD OFF
  // ============================================================

  private readonly leadOffSubject =
    new BehaviorSubject<boolean>(false);

  readonly leadOff$: Observable<boolean> =
    this.leadOffSubject.asObservable();

  // ============================================================
  // PPG
  // ============================================================

  private readonly ppgSubject =
    new BehaviorSubject<PPGData | null>(null);

  readonly ppg$: Observable<PPGData | null> =
    this.ppgSubject.asObservable();

  // ============================================================
  // IMU
  // ============================================================

  private readonly imuSubject =
    new BehaviorSubject<IMUData | null>(null);

  readonly imu$: Observable<IMUData | null> =
    this.imuSubject.asObservable();

  // ============================================================
  // BATTERY
  // ============================================================

  private readonly batterySubject =
    new BehaviorSubject<BatteryData | null>(null);

  readonly battery$: Observable<BatteryData | null> =
    this.batterySubject.asObservable();

  // ============================================================
  // LAST UPDATE
  // ============================================================

  private readonly lastUpdateSubject =
    new BehaviorSubject<Date | null>(null);

  readonly lastUpdate$: Observable<Date | null> =
    this.lastUpdateSubject.asObservable();

  // ============================================================
  // CONSTRUCTOR
  // ============================================================

  constructor(
    private readonly esp32Service: Esp32WebsocketService
  ) {

    this.subscribeToEsp32();
  }

  // ============================================================
  // SUBSCRIBE TO ESP32
  // ============================================================

  private subscribeToEsp32(): void {

    this.esp32Service.jsonPackets$
      .pipe(
        takeUntil(this.destroy$)
      )
      .subscribe({
        next: (packet) => {

          this.processPacket(packet);
        },

        error: (error) => {

          console.error(
            '[WearableDataService] ESP32 stream error:',
            error
          );
        }
      });
  }

  // ============================================================
  // PROCESS COMPLETE PACKET
  // ============================================================

  private processPacket(
    packet: WearablePacket
  ): void {

    // ----------------------------------------------------------
    // Store complete packet
    // ----------------------------------------------------------

    this.packetSubject.next(packet);

    // ----------------------------------------------------------
    // VITALS
    // ----------------------------------------------------------

    if (packet.vitals) {

      this.vitalsSubject.next(packet.vitals);

      this.heartRateSubject.next(
        packet.vitals.heart_rate
      );

      this.spo2Subject.next(
        packet.vitals.spo2
      );

      this.temperatureSubject.next(
        packet.vitals.temperature
      );
    }

    // ----------------------------------------------------------
    // ECG
    // ----------------------------------------------------------

    if (packet.ecg) {

      this.ecgSubject.next(packet.ecg);

      this.signalQualitySubject.next(
        packet.ecg.signal_quality
      );

      this.noiseLevelSubject.next(
        packet.ecg.noise_level
      );

      this.leadOffSubject.next(
        packet.ecg.lead_off
      );
    }

    // ----------------------------------------------------------
    // PPG
    // ----------------------------------------------------------

    if (packet.ppg) {

      this.ppgSubject.next(packet.ppg);
    }

    // ----------------------------------------------------------
    // IMU
    // ----------------------------------------------------------

    if (packet.imu) {

      this.imuSubject.next(packet.imu);
    }

    // ----------------------------------------------------------
    // BATTERY
    // ----------------------------------------------------------

    if (packet.battery) {

      this.batterySubject.next(packet.battery);
    }

    // ----------------------------------------------------------
    // UPDATE TIME
    // ----------------------------------------------------------

    this.lastUpdateSubject.next(
      new Date()
    );
  }

  // ============================================================
  // GET CURRENT VALUES
  // ============================================================

  getCurrentPacket(): WearablePacket | null {

    return this.packetSubject.value;
  }

  getCurrentHeartRate(): number | null {

    return this.heartRateSubject.value;
  }

  getCurrentSpO2(): number | null {

    return this.spo2Subject.value;
  }

  getCurrentTemperature(): number | null {

    return this.temperatureSubject.value;
  }

  getCurrentBattery(): BatteryData | null {

    return this.batterySubject.value;
  }

  getCurrentIMU(): IMUData | null {

    return this.imuSubject.value;
  }

  getCurrentPPG(): PPGData | null {

    return this.ppgSubject.value;
  }

  getCurrentECGData(): ECGData | null {

    return this.ecgSubject.value;
  }

  // ============================================================
  // CLEANUP
  // ============================================================

  ngOnDestroy(): void {

    this.destroy$.next();

    this.destroy$.complete();

    this.packetSubject.complete();

    this.vitalsSubject.complete();

    this.heartRateSubject.complete();

    this.spo2Subject.complete();

    this.temperatureSubject.complete();

    this.ecgSubject.complete();

    this.signalQualitySubject.complete();

    this.noiseLevelSubject.complete();

    this.leadOffSubject.complete();

    this.ppgSubject.complete();

    this.imuSubject.complete();

    this.batterySubject.complete();

    this.lastUpdateSubject.complete();
  }
}