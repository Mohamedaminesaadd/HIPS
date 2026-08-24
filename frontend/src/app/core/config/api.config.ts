import { InjectionToken } from '@angular/core';

/**
 * Base URL for the HPIS FastAPI application.
 *
 * Override this token in an environment-specific application config when the
 * API is deployed somewhere other than the local development server.
 */
export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL', {
  providedIn: 'root',
  factory: () => 'http://localhost:8000',
});

/** Replace with the authenticated wearable owner when authentication is added. */
export const ECG_TRANSPORT_SUBJECT_ID = new InjectionToken<string>(
  'ECG_TRANSPORT_SUBJECT_ID',
  {
    providedIn: 'root',
    factory: () => 'test-subject',
  },
);
