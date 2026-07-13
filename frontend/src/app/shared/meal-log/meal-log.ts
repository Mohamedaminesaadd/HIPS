import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

import { MealItem } from '../meal-item/meal-item';

export interface FoodItem {

  name: string;

  quantity: string;

  calories: number;

}

export interface Meal {

  id: string;

  name: string;

  time: string;

  icon: string;

  calories: number;

  proteins: number;

  carbs: number;

  fats: number;

  expanded: boolean;

  foods: FoodItem[];

}

@Component({
  selector: 'app-meal-log',
  standalone: true,
  imports: [
    CommonModule,
    MealItem
  ],
  templateUrl: './meal-log.html',
  styleUrl: './meal-log.css'
})
export class MealLog {

  meals: Meal[] = [

    {
      id: 'breakfast',

      name: 'Petit-déjeuner',

      time: '07:30',

      icon: 'breakfast_dining',

      calories: 620,

      proteins: 30,

      carbs: 91,

      fats: 17,

      expanded: true,

      foods: [

        {
          name: 'Flocons d’avoine',
          quantity: '80 g',
          calories: 302
        },

        {
          name: 'Banane',
          quantity: '1 moyenne',
          calories: 105
        },

        {
          name: 'Lait demi-écrémé',
          quantity: '250 ml',
          calories: 118
        },

        {
          name: 'Whey',
          quantity: '30 g',
          calories: 95
        }

      ]

    },

    {
      id: 'lunch',

      name: 'Déjeuner',

      time: '12:45',

      icon: 'lunch_dining',

      calories: 740,

      proteins: 48,

      carbs: 72,

      fats: 20,

      expanded: false,

      foods: []

    },

    {
      id: 'snack',

      name: 'Collation',

      time: '16:30',

      icon: 'cookie',

      calories: 280,

      proteins: 24,

      carbs: 25,

      fats: 8,

      expanded: false,

      foods: []

    },

    {
      id: 'dinner',

      name: 'Dîner',

      time: '20:15',

      icon: 'dinner_dining',

      calories: 520,

      proteins: 36,

      carbs: 40,

      fats: 18,

      expanded: false,

      foods: []

    }

  ];

  toggle(meal: Meal): void {

    meal.expanded = !meal.expanded;

  }

}