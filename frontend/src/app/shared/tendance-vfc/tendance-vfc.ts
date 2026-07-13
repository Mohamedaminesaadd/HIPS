import { Component } from '@angular/core';
import {
  ApexAxisChartSeries,
  ApexChart,
  ApexXAxis,
  ApexYAxis,
  ApexDataLabels,
  ApexPlotOptions,
  ApexFill,
  ApexGrid,
  ApexTooltip,
  ApexStates,
  NgApexchartsModule,
} from 'ng-apexcharts';

export type VfcChartOptions = {
  series: ApexAxisChartSeries;
  chart: ApexChart;
  xaxis: ApexXAxis;
  yaxis: ApexYAxis | ApexYAxis[];
  dataLabels: ApexDataLabels;
  plotOptions: ApexPlotOptions;
  fill: ApexFill;
  grid: ApexGrid;
  tooltip: ApexTooltip;
  states: ApexStates;
  colors: string[];
};

@Component({
  selector: 'app-vfc-chart',
  standalone: true,
  imports: [NgApexchartsModule],
  templateUrl: './tendance-vfc.html',
  styleUrl: './tendance-vfc.css',
})
export class VfcChart {
  // ── Données statiques (à brancher plus tard sur l'API) ──
  readonly days   = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
  readonly values = [52, 58, 61, 41, 63, 64, 68];

  get average(): number {
    const avg = this.values.reduce((a, b) => a + b, 0) / this.values.length;
    return Math.round(avg * 10) / 10; // 1 décimale
  }

  // index de la dernière barre à mettre en avant (teal)
  private readonly highlightIndex = this.values.length - 1;

  public chartOptions: VfcChartOptions = {
    series: [
      {
        name: 'VFC',
        data: this.values,
      },
    ],
    chart: {
      type: 'bar',
      height: 240,
      fontFamily: 'DM Sans, sans-serif',
      background: 'transparent',
      toolbar: { show: false },
      animations: {
        enabled: true,
        speed: 500,
      },
    },
    colors: ['#2A3A5C'],
    plotOptions: {
      bar: {
        columnWidth: '52%',
        borderRadius: 6,
        borderRadiusApplication: 'end',
        distributed: true, // permet une couleur par barre
      },
    },
    // couleur par barre : la dernière en teal, les autres en navy
    fill: {
      opacity: 1,
      colors: this.values.map((_, i) =>
        i === this.highlightIndex ? '#2DD4BF' : '#2A3A5C'
      ),
    } as ApexFill,
    dataLabels: {
      enabled: true,
      // n'afficher que la valeur de la barre mise en avant
      formatter: (val: number, opts: any) =>
        opts.dataPointIndex === this.highlightIndex ? `${val}` : '',
      offsetY: -20,
      style: {
        fontSize: '13px',
        fontWeight: '700',
        colors: ['#2DD4BF'],
      },
    },
    grid: {
      show: true,
      borderColor: 'rgba(148,163,184,0.08)',
      strokeDashArray: 4,
      yaxis: { lines: { show: true } },
      xaxis: { lines: { show: false } },
      padding: { top: 10, right: 0, bottom: 0, left: 0 },
    },
    xaxis: {
      categories: this.days,
      axisBorder: { show: false },
      axisTicks: { show: false },
      labels: {
        style: {
          colors: '#94A3B8',
          fontSize: '12px',
          fontWeight: '500',
        },
      },
    },
    yaxis: {
      show: false,
    },
    tooltip: {
      theme: 'dark',
      y: {
        formatter: (val: number) => `${val} ms`,
      },
    },
    states: {
      hover: { filter: { type: 'lighten'} },
      active: { filter: { type: 'none' } },
    },
  };
}