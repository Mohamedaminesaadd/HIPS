import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatRippleModule } from '@angular/material/core';

@Component({
  selector: 'app-stats-row-training',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatRippleModule],
  templateUrl: './stats-row-training.html',
  styleUrl: './stats-row-training.css',
})
export class StatsRowTraining {

  // ── VOLUME TOTAL ──
  totalVolume = 12130;   // kg
  volumeTrend = 6;       // % vs dernière séance

  // ── 1RM ESTIMÉ ──
  exerciseName = 'SQUAT';
  oneRm = 140;           // kg
  oneRmGoal = 150;       // kg

  // ── SÉRIES EFFECTUÉES ──
  setsDone = 18;
  setsTarget = 20;

  get oneRmPercent(): number {
    if (this.oneRmGoal <= 0) return 0;
    return Math.min(100, Math.max(0, (this.oneRm / this.oneRmGoal) * 100));
  }

  get setsPercent(): number {
    if (this.setsTarget <= 0) return 0;
    return Math.min(100, Math.max(0, (this.setsDone / this.setsTarget) * 100));
  }

  get isVolumeUp(): boolean {
    return this.volumeTrend >= 0;
  }

  /** Formatage FR sans dépendre de registerLocaleData (espace fine comme séparateur). */
  get volumeFormatted(): string {
    return this.totalVolume.toLocaleString('fr-FR');
  }
}