import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL } from '../config/api.config';
import {
  EcgAnalysisRequest,
  EcgAnalysisResponse,
} from '../models/ecg-analysis.model';

@Injectable({
  providedIn: 'root',
})
export class EcgApiService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = inject(API_BASE_URL);

  analyzeEcg(payload: EcgAnalysisRequest): Observable<EcgAnalysisResponse> {
    return this.http.post<EcgAnalysisResponse>(
      `${this.apiBaseUrl}/api/ecg/analyze`,
      payload,
    );
  }
}
