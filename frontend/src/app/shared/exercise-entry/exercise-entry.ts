import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

import { MatIconModule } from '@angular/material/icon';
import { MatRippleModule } from '@angular/material/core';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';

import { AddExerciseDialog } from '../add-exercice-dialog/add-exercice-dialog';

export interface SetEntry {
  setNumber: number;
  weight: number;
  reps: number;
  rpe: string | null;
  velocity: string;
  status: 'warmup' | 'pr' | null;
}

export interface OneRmPoint {
  value: number;
  label?: string;
}

export interface ExerciseEntry {
  id: string;
  name: string;
  topSet: string;
  totalVolume: number;
  expanded: boolean;
  sets?: SetEntry[];
  oneRmHistory?: OneRmPoint[];
  oneRmEstimated?: number;
  blockGoal?: number;
}

@Component({
  selector: 'app-exercise-log',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatRippleModule,
    MatDialogModule
  ],
  templateUrl: './exercise-entry.html',
  styleUrl: './exercise-entry.css',
})
export class ExerciseLog {

  constructor(
    private dialog: MatDialog
  ) {}

  @Input() exercises: ExerciseEntry[] = [
    {
      id: 'squat-barre',
      name: 'Squat barre',
      topSet: 'Top set : 120 kg × 5 @ RPE 8',
      totalVolume: 3010,
      expanded: true,
      sets: [
        { setNumber: 1, weight: 60, reps: 8, rpe: null, velocity: '0,82', status: 'warmup' },
        { setNumber: 2, weight: 80, reps: 5, rpe: null, velocity: '0,68', status: 'warmup' },
        { setNumber: 3, weight: 100, reps: 5, rpe: '7', velocity: '0,62', status: null },
        { setNumber: 4, weight: 110, reps: 5, rpe: '7,5', velocity: '0,55', status: null },
        { setNumber: 5, weight: 120, reps: 5, rpe: '8', velocity: '0,48', status: 'pr' },
        { setNumber: 6, weight: 120, reps: 4, rpe: '8,5', velocity: '0,44', status: null },
      ],
      oneRmHistory: [
        { value: 128, label: 'Avril' },
        { value: 129 },
        { value: 130 },
        { value: 132 },
        { value: 131, label: 'Mai' },
        { value: 133 },
        { value: 135 },
        { value: 136 },
        { value: 135, label: 'Juin' },
        { value: 137 },
        { value: 138 },
        { value: 139 },
        { value: 140, label: 'Juillet' },
      ],
      oneRmEstimated: 140,
      blockGoal: 150,
    },
    {
      id: 'presse-cuisses',
      name: 'Presse à cuisses',
      topSet: 'Top set : 200 kg × 8 @ RPE 8',
      totalVolume: 5860,
      expanded: false,
    },
    {
      id: 'fentes-bulgares',
      name: 'Fentes bulgares',
      topSet: 'Top set : 40 kg × 8 @ RPE 7',
      totalVolume: 1240,
      expanded: false,
    },
    {
      id: 'leg-curl',
      name: 'Leg curl',
      topSet: 'Top set : 50 kg × 10 @ RPE 8',
      totalVolume: 2020,
      expanded: false,
    },
  ];

  private readonly chartWidth = 1000;
  private readonly chartHeight = 120;
  private readonly chartPadX = 4;
  private readonly chartPadY = 14;

  toggle(exercise: ExerciseEntry): void {
    exercise.expanded = !exercise.expanded;
  }

  private getChartPoints(exercise: ExerciseEntry): { x: number; y: number }[] {

    const data = exercise.oneRmHistory ?? [];

    if (!data.length) return [];

    const values = data.map(d => d.value);

    const min = Math.min(...values);
    const max = Math.max(...values);

    const range = max - min || 1;

    const usableW = this.chartWidth - this.chartPadX * 2;
    const usableH = this.chartHeight - this.chartPadY * 2;

    const denom = data.length > 1 ? data.length - 1 : 1;

    return data.map((d, i) => ({
      x: this.chartPadX + (i / denom) * usableW,
      y: this.chartPadY + usableH - ((d.value - min) / range) * usableH,
    }));
  }

  getSmoothPath(exercise: ExerciseEntry): string {

    const pts = this.getChartPoints(exercise);

    if (pts.length < 2) return '';

    let d = `M ${pts[0].x.toFixed(1)},${pts[0].y.toFixed(1)}`;

    for (let i = 0; i < pts.length - 1; i++) {

      const p0 = pts[i === 0 ? i : i - 1];
      const p1 = pts[i];
      const p2 = pts[i + 1];
      const p3 = pts[i + 2 < pts.length ? i + 2 : i + 1];

      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;

      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;

      d += ` C ${cp1x.toFixed(1)},${cp1y.toFixed(1)} ${cp2x.toFixed(1)},${cp2y.toFixed(1)} ${p2.x.toFixed(1)},${p2.y.toFixed(1)}`;
    }

    return d;
  }

  getLastPoint(exercise: ExerciseEntry) {

    const pts = this.getChartPoints(exercise);

    return pts.length ? pts[pts.length - 1] : null;
  }

  getAxisLabels(exercise: ExerciseEntry): string[] {

    return (exercise.oneRmHistory ?? [])
      .map(d => d.label)
      .filter((label): label is string => !!label);
  }

  getOneRmPercent(exercise: ExerciseEntry): number {

    if (!exercise.oneRmEstimated || !exercise.blockGoal) return 0;

    return Math.min(
      100,
      Math.round((exercise.oneRmEstimated / exercise.blockGoal) * 100)
    );
  }

  openAddExerciseDialog(): void {

    const dialogRef = this.dialog.open(AddExerciseDialog, {

      width: '500px',

      disableClose: true,

      autoFocus: true

    });

    dialogRef.afterClosed().subscribe(result => {

      if (!result) return;

      this.exercises.push(result);

    });

  }

}