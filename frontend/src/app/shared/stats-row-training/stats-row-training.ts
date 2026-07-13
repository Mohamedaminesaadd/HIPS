import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatRippleModule } from '@angular/material/core';

@Component({
  selector: 'app-stats-row-training',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatRippleModule
  ],
  templateUrl: './stats-row-training.html',
  styleUrl: './stats-row-training.css',
})
export class StatsRowTraining {

  // Volume total
  totalVolume = 12130;
  volumeTrend = 6;

  // 1RM estimé
  exerciseName = 'SQUAT';
  oneRm = 140;
  oneRmGoal = 150;

  // Séries effectuées
  setsDone = 18;
  setsTarget = 20;

  get oneRmPercent(): number {
    return Math.min(100, (this.oneRm / this.oneRmGoal) * 100);
  }

  get setsPercent(): number {
    return Math.min(100, (this.setsDone / this.setsTarget) * 100);
  }
}