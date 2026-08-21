export interface Insight {
  user_id: string;
  timestamp: string;

  stress?: {
    score: number;
    level: string;
  };

  cardiac?: {
    heart_rate: number;
    status: string;
  };

  spo2?: {
    value: number;
    status: string;
  };

  sleep?: {
    score: number;
    status: string;
  };
}