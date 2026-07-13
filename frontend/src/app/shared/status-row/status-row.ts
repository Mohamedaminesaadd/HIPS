import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatRippleModule } from '@angular/material/core';

@Component({
  selector: 'app-stats-row',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatRippleModule
  ],
  templateUrl: './status-row.html',
  styleUrl: './status-row.css',
})
export class StatsRow {

  recovery = 82;
  recoveryTrend = 6;

  rmssd = 68;
  rmssdTrend = 8;

  restingHeartRate = 47;
  restingTrend = -2;

  sleepHours = "7 h 42";
  sleepEfficiency = 91;
  deepSleep = "1 h 38";

}