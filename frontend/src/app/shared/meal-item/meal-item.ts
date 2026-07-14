import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatRippleModule } from '@angular/material/core';

export interface FoodItem {
  name: string;
  quantity: string;
  calories: number;
  proteins: number;
  carbs: number;
  fats: number;
}

export interface Meal {
  id: string;
  name: string;
  time?: string;
  icon: string;
  accent: string;          // couleur d'accent (hex) pour l'icône
  status?: string;         // ex. 'À venir' — sinon on affiche les kcal
  calories: number;
  proteins: number;
  carbs: number;
  fats: number;
  // Objectifs — utilisés pour l'état vide (reste à couvrir)
  targetCalories?: number;
  targetProteins?: number;
  targetCarbs?: number;
  expanded: boolean;
  foods: FoodItem[];
}

@Component({
  selector: 'app-meal-item',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatRippleModule],
  templateUrl: './meal-item.html',
  styleUrl: './meal-item.css',
})
export class MealItem {
  @Input({ required: true }) meal!: Meal;

  /** Émis quand l'utilisateur clique sur « Planifier avec l'IA ». */
  @Output() plan = new EventEmitter<Meal>();

  get hasFoods(): boolean {
    return this.meal.foods.length > 0;
  }

  get remainingKcal(): number {
    return Math.max(0, (this.meal.targetCalories ?? 0) - this.meal.calories);
  }

  get remainingProteins(): number {
    return Math.max(0, (this.meal.targetProteins ?? 0) - this.meal.proteins);
  }

  get remainingCarbs(): number {
    return Math.max(0, (this.meal.targetCarbs ?? 0) - this.meal.carbs);
  }

  toggle(): void {
    this.meal.expanded = !this.meal.expanded;
  }

  addFood(): void {
    console.log('Ajouter aliment', this.meal.id);
  }

  deleteFood(food: FoodItem): void {
    this.meal.foods = this.meal.foods.filter((f) => f !== food);
  }

  planWithAI(): void {
    this.plan.emit(this.meal);
  }
}