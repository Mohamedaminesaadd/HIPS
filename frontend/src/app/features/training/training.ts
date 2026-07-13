import { Component } from '@angular/core';
import { StatsRowTraining } from "../../shared/stats-row-training/stats-row-training";
import { PlateauAlertComponent } from "../../shared/plateau-alert-component/plateau-alert-component";
import { ExerciseLog } from "../../shared/exercise-entry/exercise-entry";

@Component({
  selector: 'app-training',
  imports: [StatsRowTraining, PlateauAlertComponent, ExerciseLog],
  templateUrl: './training.html',
  styleUrl: './training.css',
})
export class Training {

}
