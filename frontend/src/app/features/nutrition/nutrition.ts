import { Component } from '@angular/core';
import { NutritionHeader } from "../../shared/nutrition-header/nutrition-header";
import { NutritionStats } from "../../shared/nutrition-stats/nutrition-stats";
import { MealLog } from "../../shared/meal-log/meal-log";
import { NutritionAlerts } from "../../shared/nutrition-alerts/nutrition-alerts";

@Component({
  selector: 'app-nutrition',
  imports: [NutritionHeader, NutritionStats, MealLog, NutritionAlerts],
  templateUrl: './nutrition.html',
  styleUrl: './nutrition.css',
})
export class Nutrition {

}
