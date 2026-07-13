import { Component } from '@angular/core';

import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import {
  MatDialogModule,
  MatDialogRef
} from '@angular/material/dialog';

import { MatButtonModule } from '@angular/material/button';

import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

@Component({
  selector: 'app-add-exercise-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,

    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule
  ],
  templateUrl: './add-exercice-dialog.html',
  styleUrl: './add-exercice-dialog.css'
})
export class AddExerciseDialog {

  exerciseName = '';

  constructor(

    private dialogRef: MatDialogRef<AddExerciseDialog>

  ){}

  cancel(): void {

    this.dialogRef.close();

  }

  save(): void {

    this.dialogRef.close({

      id: crypto.randomUUID(),

      name: this.exerciseName,

      topSet: '',

      totalVolume: 0,

      expanded: false,

      sets: [],

      oneRmHistory: []

    });

  }

}