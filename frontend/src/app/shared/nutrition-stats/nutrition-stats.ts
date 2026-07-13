import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatRippleModule } from '@angular/material/core';

@Component({
  selector: 'app-nutrition-stats',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatRippleModule
  ],
  templateUrl: './nutrition-stats.html',
  styleUrl: './nutrition-stats.css'
})
export class NutritionStats {

  // ============================
  // Calories
  // ============================

  calories = 1640;
  caloriesGoal = 2450;

  // ============================
  // Protéines
  // ============================

  proteins = 105;
  proteinsGoal = 150;

  // ============================
  // Glucides
  // ============================

  carbs = 218;
  carbsGoal = 280;

  // ============================
  // Lipides
  // ============================

  fats = 42;
  fatsGoal = 80;

  // ============================
  // Hydratation
  // ============================

  water = 1.8;
  waterGoal = 3.0;

  // ============================
  // Calculs
  // ============================

  get caloriesPercent(): number {

    return Math.min(
      100,
      Math.round(this.calories / this.caloriesGoal * 100)
    );

  }

  get proteinsPercent(): number {

    return Math.min(
      100,
      Math.round(this.proteins / this.proteinsGoal * 100)
    );

  }

  get carbsPercent(): number {

    return Math.min(
      100,
      Math.round(this.carbs / this.carbsGoal * 100)
    );

  }

  get fatsPercent(): number {

    return Math.min(
      100,
      Math.round(this.fats / this.fatsGoal * 100)
    );

  }

  get waterPercent(): number {

    return Math.min(
      100,
      Math.round(this.water / this.waterGoal * 100)
    );

  }

  // ============================
  // Informations
  // ============================

  get remainingProteins(): number {

    return this.proteinsGoal - this.proteins;

  }

  get hydrationDifference(): number {

    return +(this.waterGoal - this.water).toFixed(1);

  }

}