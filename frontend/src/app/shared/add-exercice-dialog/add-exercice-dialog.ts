import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

export type MuscleKey =
  | 'jambes' | 'pectoraux' | 'dos' | 'epaules'
  | 'biceps' | 'triceps' | 'abdos' | 'cardio';

export interface MuscleInfo {
  key: MuscleKey;
  label: string;
  icon: string;
  color: string;
}

export const MUSCLES: MuscleInfo[] = [
  { key: 'jambes',    label: 'Jambes',    icon: 'directions_run',   color: '#3B82F6' },
  { key: 'pectoraux', label: 'Pectoraux', icon: 'favorite',         color: '#F87171' },
  { key: 'dos',       label: 'Dos',       icon: 'rowing',           color: '#2DD4BF' },
  { key: 'epaules',   label: 'Épaules',   icon: 'accessibility_new',color: '#FBBF24' },
  { key: 'biceps',    label: 'Biceps',    icon: 'fitness_center',   color: '#A78BFA' },
  { key: 'triceps',   label: 'Triceps',   icon: 'bolt',             color: '#FB923C' },
  { key: 'abdos',     label: 'Abdos',     icon: 'self_improvement', color: '#34D399' },
  { key: 'cardio',    label: 'Cardio',    icon: 'directions_bike',  color: '#60A5FA' },
];

@Component({
  selector: 'app-add-exercise-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, MatDialogModule, MatIconModule],
  templateUrl: './add-exercice-dialog.html',
  styleUrl: './add-exercice-dialog.css',
})
export class AddExerciseDialog {
  muscles = MUSCLES;

  exerciseName = '';
  selectedMuscle: MuscleKey | null = null;

  constructor(private dialogRef: MatDialogRef<AddExerciseDialog>) {}

  get canSave(): boolean {
    return this.exerciseName.trim().length > 0 && this.selectedMuscle !== null;
  }

  select(key: MuscleKey): void {
    this.selectedMuscle = key;
  }

  cancel(): void {
    this.dialogRef.close();
  }

  save(): void {
    if (!this.canSave) return;

    this.dialogRef.close({
      id: crypto.randomUUID(),
      name: this.exerciseName.trim(),
      muscle: this.selectedMuscle,
      topSet: '',
      totalVolume: 0,
      expanded: true,
      sets: [],
      oneRmHistory: [],
    });
  }
}