import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { Insight } from '../models/insight.model';

@Injectable({
  providedIn: 'root'
})
export class InsightsService {

  private readonly apiUrl = 'http://localhost:8000/insights';

  constructor(
    private readonly http: HttpClient
  ) {}

  getLatestInsight(
    userId: string
  ): Observable<Insight> {

    return this.http.get<Insight>(
      `${this.apiUrl}/users/${userId}/latest`
    );
  }
}