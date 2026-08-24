export interface EcgAnalysisRequest {
  subject_id: string;
  timestamp: number;
  ecg: {
    fs: number;
    samples: number[];
  };
  vitals: {
    hr: number | null;
    spo2: number | null;
    temperature: number | null;
  };
  quality: {
    ecg_quality: number | null;
    noise: number | null;
    lead_off: boolean;
  };
}

/** Interim transport response; it intentionally contains no diagnosis. */
export interface EcgAnalysisResponse {
  subject_id: string;
  status: 'received';
  ecg_samples: number;
  sampling_rate: number;
  window_seconds: number;
  signal_quality: number | null;
}
