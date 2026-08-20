// ============================================================
// HPIS WEARABLE DATA MODELS
// ============================================================

export interface WearablePacket {
  packet_version: string;
  packet: number;
  timestamp_ms: number;

  ecg: ECGData;

  ppg: PPGData;

  vitals: VitalsData;

  imu: IMUData;

  battery: BatteryData;
}

// ============================================================
// ECG
// ============================================================

export interface ECGData {
  sample_rate: number;

  lead_off: boolean;

  signal_quality: number;

  noise_level: number;

  samples: number[];
}

// ============================================================
// PPG
// ============================================================

export interface PPGData {
  red: number;

  ir: number;
}

// ============================================================
// VITALS
// ============================================================

export interface VitalsData {
  heart_rate: number;

  spo2: number;

  temperature: number;
}

// ============================================================
// IMU
// ============================================================

export interface IMUData {
  acc: AccelerationData;

  gyro: GyroscopeData;
}

export interface AccelerationData {
  x: number;

  y: number;

  z: number;
}

export interface GyroscopeData {
  x: number;

  y: number;

  z: number;
}

// ============================================================
// BATTERY
// ============================================================

export interface BatteryData {
  level: number;

  voltage: number;
}

// ============================================================
// ECG CHUNK
// ============================================================

export interface ECGChunk {
  samples: number[];
}

// ============================================================
// CONNECTION STATUS
// ============================================================

export interface ESP32ConnectionState {
  connected: boolean;

  reconnecting: boolean;

  error: boolean;
}