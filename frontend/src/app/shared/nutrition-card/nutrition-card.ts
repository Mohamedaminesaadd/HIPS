import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

interface Macro {
  label: string;
  value: number;
  unit: string;
  max: number;
  color: string;
}

@Component({
  selector: 'app-nutrition-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './nutrition-card.html',
  styleUrls: ['./nutrition-card.css']
})
export class NutritionCardComponent {
  @Input() title: string = "NUTRITION · AUJOURD'HUI";
  @Input() calories: number = 2840;
  @Input() calorieGoal: number = 3100;

  @Input() macros: Macro[] = [
    { label: 'Protéines', value: 142, unit: 'g', max: 180, color: '#2dd4bf' },
    { label: 'Glucides', value: 348, unit: 'g', max: 400, color: '#38bdf8' },
    { label: 'Lipides',  value: 86,  unit: 'g', max: 100, color: '#f59e0b' }
  ];

  get caloriePercent(): number {
    return Math.min(100, (this.calories / this.calorieGoal) * 100);
  }

  getMacroPercent(macro: Macro): number {
    return Math.min(100, (macro.value / macro.max) * 100);
  }
}