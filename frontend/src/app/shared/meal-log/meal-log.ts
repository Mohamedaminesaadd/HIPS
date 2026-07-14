import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MealItem, Meal } from '../meal-item/meal-item';

@Component({
  selector: 'app-meal-log',
  standalone: true,
  imports: [CommonModule, MealItem],
  templateUrl: './meal-log.html',
  styleUrl: './meal-log.css',
})
export class MealLog {
  meals: Meal[] = [
    {
      id: 'breakfast',
      name: 'Petit-déjeuner',
      icon: 'bakery_dining',
      accent: '#FBBF24',
      calories: 620,
      proteins: 30,
      carbs: 91,
      fats: 17,
      expanded: true,
      foods: [
        { name: "Flocons d'avoine", quantity: '80 g',            calories: 304, proteins: 10, carbs: 54, fats: 6 },
        { name: 'Yaourt grec 2 %',  quantity: '150 g',           calories: 110, proteins: 15, carbs: 6,  fats: 3 },
        { name: 'Banane',           quantity: '1 portion (120 g)', calories: 107, proteins: 1,  carbs: 27, fats: 0 },
        { name: 'Amandes',          quantity: '17 g',            calories: 99,  proteins: 4,  carbs: 4,  fats: 8 },
      ],
    },
    {
      id: 'lunch',
      name: 'Déjeuner',
      icon: 'lunch_dining',
      accent: '#3B82F6',
      calories: 740,
      proteins: 51,
      carbs: 83,
      fats: 23,
      expanded: false,
      foods: [
        { name: 'Poulet grillé',        quantity: '150 g', calories: 248, proteins: 46, carbs: 0,  fats: 6 },
        { name: 'Riz basmati (cuit)',   quantity: '200 g', calories: 260, proteins: 5,  carbs: 56, fats: 1 },
        { name: "Huile d'olive",        quantity: '15 g',  calories: 132, proteins: 0,  carbs: 0,  fats: 15 },
        { name: 'Légumes vapeur',       quantity: '200 g', calories: 100, proteins: 4,  carbs: 20, fats: 1 },
      ],
    },
    {
      id: 'snack',
      name: 'Collation pré-séance',
      icon: 'cookie',
      accent: '#2DD4BF',
      calories: 280,
      proteins: 24,
      carbs: 44,
      fats: 2,
      expanded: false,
      foods: [
        { name: 'Whey isolate', quantity: '30 g',  calories: 116, proteins: 24, carbs: 3,  fats: 1 },
        { name: 'Banane',       quantity: '120 g', calories: 107, proteins: 1,  carbs: 27, fats: 0 },
        { name: 'Miel',         quantity: '15 g',  calories: 46,  proteins: 0,  carbs: 12, fats: 0 },
      ],
    },
    {
      id: 'dinner',
      name: 'Dîner',
      icon: 'dinner_dining',
      accent: '#2DD4BF',
      status: 'À venir',
      calories: 0,
      proteins: 0,
      carbs: 0,
      fats: 0,
      targetCalories: 810,
      targetProteins: 45,
      targetCarbs: 62,
      expanded: false,
      foods: [],
    },
  ];

  onPlan(meal: Meal): void {
    // TODO : brancher sur l'Agent Nutrition (IA)
    console.log('Planifier avec l\'IA →', meal.name);
  }
}