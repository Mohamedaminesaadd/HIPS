import { DecimalPipe, isPlatformBrowser } from '@angular/common';
import { Component, DestroyRef, OnInit, PLATFORM_ID, inject } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import {
  ApexAxisChartSeries,
  ApexChart,
  ApexGrid,
  ApexStroke,
  ApexTooltip,
  ApexXAxis,
  ApexYAxis,
  NgApexchartsModule,
} from 'ng-apexcharts';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { EcgProcessingService } from '../../core/services/ecg-processing.service';
import { Esp32WebsocketService } from '../../core/services/esp32-websocket.service';
import { WearableDataService } from '../../core/services/wearable-data.service';

/**
 * Contract reserved for the future FastAPI cardiac-analysis response.
 * No prediction is created on the client while that endpoint is unavailable.
 */
export interface CardiacAnalysisResult {
  cardiacState: string;
  confidence: number;
  abnormality?: string | null;
}

type EcgChartOptions = {
  series: ApexAxisChartSeries;
  chart: ApexChart;
  xaxis: ApexXAxis;
  yaxis: ApexYAxis;
  grid: ApexGrid;
  stroke: ApexStroke;
  tooltip: ApexTooltip;
  colors: string[];
};

@Component({
  selector: 'app-cardiac',
  standalone: true,
  imports: [DecimalPipe, MatIconModule, NgApexchartsModule],
  templateUrl: './cardiac.html',
  styleUrl: './cardiac.css',
})
export class Cardiac implements OnInit {

  private readonly destroyRef = inject(DestroyRef);
  private readonly platformId = inject(PLATFORM_ID);
  readonly sampleRate = 250;

  connected = false;
  connecting = false;
  connectionError = false;
  leadOff = false;
  hasEcgData = false;
  signalQuality: number | null = null;
  calculatedHeartRate: number | null = null;
  wearableHeartRate: number | null = null;
  analysisResult: CardiacAnalysisResult | null = null;

  chartOptions: EcgChartOptions = {
    series: [{ name: 'ECG', data: [] }],
    chart: {
      type: 'line',
      height: 310,
      background: 'transparent',
      toolbar: { show: false },
      animations: { enabled: false },
      zoom: { enabled: false },
    },
    colors: ['#2DD4BF'],
    stroke: { curve: 'smooth', width: 2 },
    grid: {
      borderColor: 'rgba(45, 212, 191, 0.12)',
      strokeDashArray: 3,
      padding: { top: 8, right: 6, bottom: 0, left: 6 },
    },
    xaxis: {
      type: 'numeric',
      min: -3,
      max: 0,
      tickAmount: 3,
      axisBorder: { show: false },
      axisTicks: { show: false },
      labels: {
        formatter: (value: string) => `${Number(value).toFixed(0)} s`,
        style: { colors: '#64748B', fontSize: '11px' },
      },
    },
    yaxis: {
      show: false,
      decimalsInFloat: 2,
    },
    tooltip: {
      theme: 'dark',
      x: { formatter: (value: number) => `${value.toFixed(2)} s` },
      y: { formatter: (value: number) => value.toFixed(2) },
    },
  };

  constructor(
    private readonly esp32Service: Esp32WebsocketService,
    private readonly ecgProcessingService: EcgProcessingService,
    private readonly wearableDataService: WearableDataService,
  ) {}

  ngOnInit(): void {
    this.subscribeToLiveData();

    if (isPlatformBrowser(this.platformId)) {
      this.connecting = true;
      this.esp32Service.connect();
    }
  }

  get heartRate(): number | null {
    return this.calculatedHeartRate ?? this.wearableHeartRate;
  }

  get connectionLabel(): string {
    if (this.connected) return 'Wearable connected';
    if (this.connecting && !this.connectionError) return 'Connecting to wearable...';
    return 'Wearable disconnected';
  }

  get qualityPercent(): number | null {
    if (this.signalQuality === null || !Number.isFinite(this.signalQuality)) return null;
    return Math.round(Math.max(0, Math.min(100, this.signalQuality <= 1 ? this.signalQuality * 100 : this.signalQuality)));
  }

  get qualityLabel(): string {
    if (this.leadOff) return 'Invalid';
    const quality = this.qualityPercent;
    if (quality === null) return 'Waiting for signal';
    if (quality >= 85) return 'Excellent';
    if (quality >= 65) return 'Good';
    return 'Poor';
  }

  get heartRateStatus(): string {
    const heartRate = this.heartRate;
    if (heartRate === null) return 'Waiting for ECG data';
    if (heartRate < 60) return 'Below resting range';
    if (heartRate > 100) return 'Above resting range';
    return 'Normal resting range';
  }

  private subscribeToLiveData(): void {
    this.esp32Service.connected$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((connected) => {
        this.connected = connected;
        this.connecting = !connected && !this.connectionError;
        if (connected) this.connectionError = false;
      });

    this.esp32Service.errors$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        this.connectionError = true;
        this.connecting = false;
      });

    this.ecgProcessingService.filteredEcg$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((samples) => {
        this.hasEcgData = samples.length > 0;
        this.updateEcgChart(samples);
      });

    this.ecgProcessingService.heartRate$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((heartRate) => (this.calculatedHeartRate = this.isValidHeartRate(heartRate) ? heartRate : null));

    this.wearableDataService.heartRate$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((heartRate) => (this.wearableHeartRate = this.isValidHeartRate(heartRate) ? heartRate : null));

    this.wearableDataService.signalQuality$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((quality) => (this.signalQuality = typeof quality === 'number' && Number.isFinite(quality) ? quality : null));

    this.wearableDataService.leadOff$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((leadOff) => (this.leadOff = leadOff));
  }

  private updateEcgChart(samples: number[]): void {
    const visibleSeconds = Math.max(1, Math.round(samples.length / this.sampleRate));
    const data = samples.map((sample, index) => ({
      x: (index - samples.length + 1) / this.sampleRate,
      y: sample,
    }));

    this.chartOptions = {
      ...this.chartOptions,
      series: [{ name: 'ECG', data }],
      xaxis: { ...this.chartOptions.xaxis, min: -visibleSeconds, max: 0 },
    };
  }

  private isValidHeartRate(value: number | null): value is number {
    return value !== null && Number.isFinite(value) && value > 0;
  }

}
