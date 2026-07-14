import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatRippleModule } from '@angular/material/core';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';

import { AddExerciseDialog, MUSCLES, MuscleKey, MuscleInfo } from '../add-exercice-dialog/add-exercice-dialog';

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
  muscle: MuscleKey;
  topSet: string;
  totalVolume: number;
  expanded: boolean;
  editing?: boolean;          // édition du nom en cours
  sets?: SetEntry[];
  oneRmHistory?: OneRmPoint[];
  oneRmEstimated?: number;
  blockGoal?: number;
}

@Component({
  selector: 'app-exercise-log',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule, MatRippleModule, MatDialogModule],
  templateUrl: './exercise-entry.html',
  styleUrl: './exercise-entry.css',
})
export class ExerciseLog {

  constructor(private dialog: MatDialog) {}

  @Input() exercises: ExerciseEntry[] = [
    {
      id: 'squat-barre',
      name: 'Squat barre',
      muscle: 'jambes',
      topSet: 'Top set : 120 kg × 5 @ RPE 8',
      totalVolume: 3010,
      expanded: true,
      sets: [
        { setNumber: 1, weight: 60,  reps: 8, rpe: null,  velocity: '0,82', status: 'warmup' },
        { setNumber: 2, weight: 80,  reps: 5, rpe: null,  velocity: '0,68', status: 'warmup' },
        { setNumber: 3, weight: 100, reps: 5, rpe: '7',   velocity: '0,62', status: null },
        { setNumber: 4, weight: 110, reps: 5, rpe: '7,5', velocity: '0,55', status: null },
        { setNumber: 5, weight: 120, reps: 5, rpe: '8',   velocity: '0,48', status: 'pr' },
        { setNumber: 6, weight: 120, reps: 4, rpe: '8,5', velocity: '0,44', status: null },
      ],
      oneRmHistory: [
        { value: 128, label: 'Avril' }, { value: 129 }, { value: 130 }, { value: 132 },
        { value: 131, label: 'Mai' },   { value: 133 }, { value: 135 }, { value: 136 },
        { value: 135, label: 'Juin' },  { value: 137 }, { value: 138 }, { value: 139 },
        { value: 140, label: 'Juillet' },
      ],
      oneRmEstimated: 140,
      blockGoal: 150,
    },
    {
      id: 'presse-cuisses',
      name: 'Presse à cuisses',
      muscle: 'jambes',
      topSet: 'Top set : 200 kg × 8 @ RPE 8',
      totalVolume: 5860,
      expanded: false,
      sets: [
        { setNumber: 1, weight: 160, reps: 10, rpe: '6',  velocity: '—', status: 'warmup' },
        { setNumber: 2, weight: 200, reps: 8,  rpe: '8',  velocity: '—', status: null },
      ],
    },
    {
      id: 'fentes-bulgares',
      name: 'Fentes bulgares',
      muscle: 'jambes',
      topSet: 'Top set : 40 kg × 8 @ RPE 7',
      totalVolume: 1240,
      expanded: false,
      sets: [],
    },
    {
      id: 'curl-biceps',
      name: 'Curl haltères',
      muscle: 'biceps',
      topSet: '',
      totalVolume: 0,
      expanded: false,
      sets: [],
    },
  ];

  // ══════════════════════════════════════════════
  //  MUSCLES
  // ══════════════════════════════════════════════
  muscleInfo(key: MuscleKey): MuscleInfo {
    return MUSCLES.find((m) => m.key === key) ?? MUSCLES[0];
  }

  // ══════════════════════════════════════════════
  //  ÉTAT ÉDITION SÉRIE
  // ══════════════════════════════════════════════
  /** Série en cours d'édition (référence) — null si aucune. */
  editingSet: SetEntry | null = null;
  /** Brouillon de la série éditée ou ajoutée. */
  draft: Partial<SetEntry> = {};
  /** Exercice dans lequel on est en train d'ajouter une série. */
  addingIn: ExerciseEntry | null = null;

  // ── Toggle carte ──
  toggle(exercise: ExerciseEntry): void {
    if (exercise.editing) return;
    exercise.expanded = !exercise.expanded;
  }

  // ══════════════════════════════════════════════
  //  CRUD EXERCICE
  // ══════════════════════════════════════════════
  startRename(exercise: ExerciseEntry, ev: Event): void {
    ev.stopPropagation();
    exercise.editing = true;
    exercise.expanded = true;
  }

  confirmRename(exercise: ExerciseEntry, newName: string): void {
    const name = newName.trim();
    if (name) exercise.name = name;
    exercise.editing = false;
  }

  deleteExercise(exercise: ExerciseEntry, ev: Event): void {
    ev.stopPropagation();
    if (!confirm(`Supprimer « ${exercise.name} » et toutes ses séries ?`)) return;
    this.exercises = this.exercises.filter((e) => e !== exercise);
  }

  // ══════════════════════════════════════════════
  //  CRUD SÉRIES
  // ══════════════════════════════════════════════
  startAddSet(exercise: ExerciseEntry): void {
    this.editingSet = null;
    this.addingIn = exercise;
    const last = exercise.sets?.[exercise.sets.length - 1];
    this.draft = {
      weight: last?.weight ?? 0,
      reps: last?.reps ?? 0,
      rpe: null,
      velocity: '—',
      status: null,
    };
  }

  startEditSet(exercise: ExerciseEntry, set: SetEntry): void {
    this.addingIn = null;
    this.editingSet = set;
    this.draft = { ...set };
  }

  cancelSetEdit(): void {
    this.editingSet = null;
    this.addingIn = null;
    this.draft = {};
  }

  saveSet(exercise: ExerciseEntry): void {
    const weight = Number(this.draft.weight) || 0;
    const reps = Number(this.draft.reps) || 0;
    if (weight <= 0 || reps <= 0) return;

    if (this.editingSet) {
      // ── UPDATE ──
      Object.assign(this.editingSet, {
        weight,
        reps,
        rpe: this.draft.rpe || null,
        velocity: this.draft.velocity || '—',
        status: this.draft.status ?? null,
      });
    } else if (this.addingIn === exercise) {
      // ── CREATE ──
      exercise.sets = exercise.sets ?? [];
      exercise.sets.push({
        setNumber: exercise.sets.length + 1,
        weight,
        reps,
        rpe: this.draft.rpe || null,
        velocity: this.draft.velocity || '—',
        status: this.draft.status ?? null,
      });
    }

    this.recompute(exercise);
    this.cancelSetEdit();
  }

  deleteSet(exercise: ExerciseEntry, set: SetEntry): void {
    exercise.sets = (exercise.sets ?? []).filter((s) => s !== set);
    exercise.sets.forEach((s, i) => (s.setNumber = i + 1));
    this.recompute(exercise);
  }

  /** Recalcule volume total et top set après tout changement. */
  private recompute(exercise: ExerciseEntry): void {
    const sets = exercise.sets ?? [];
    exercise.totalVolume = sets.reduce((sum, s) => sum + s.weight * s.reps, 0);

    const work = sets.filter((s) => s.status !== 'warmup');
    const top = [...work].sort((a, b) => b.weight - a.weight)[0];
    exercise.topSet = top
      ? `Top set : ${top.weight} kg × ${top.reps}${top.rpe ? ' @ RPE ' + top.rpe : ''}`
      : '';
  }

  // ══════════════════════════════════════════════
  //  IA
  // ══════════════════════════════════════════════
  planWithAI(exercise: ExerciseEntry): void {
    // TODO : brancher sur l'agent IA (suggestion de séries selon le bloc)
    console.log('Générer les séries avec l\'IA →', exercise.name);
  }

  // ══════════════════════════════════════════════
  //  CHART (inchangé)
  // ══════════════════════════════════════════════
  private readonly chartWidth = 1000;
  private readonly chartHeight = 120;
  private readonly chartPadX = 4;
  private readonly chartPadY = 14;

  private getChartPoints(exercise: ExerciseEntry): { x: number; y: number }[] {
    const data = exercise.oneRmHistory ?? [];
    if (!data.length) return [];

    const values = data.map((d) => d.value);
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
      .map((d) => d.label)
      .filter((label): label is string => !!label);
  }

  getOneRmPercent(exercise: ExerciseEntry): number {
    if (!exercise.oneRmEstimated || !exercise.blockGoal) return 0;
    return Math.min(100, Math.round((exercise.oneRmEstimated / exercise.blockGoal) * 100));
  }

  // ══════════════════════════════════════════════
  //  DIALOG
  // ══════════════════════════════════════════════
  openAddExerciseDialog(): void {
    const dialogRef = this.dialog.open(AddExerciseDialog, {
      width: '500px',
      disableClose: true,
      autoFocus: true,
      panelClass: 'hpis-dialog',
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (!result) return;
      this.exercises.push(result);
    });
  }
}