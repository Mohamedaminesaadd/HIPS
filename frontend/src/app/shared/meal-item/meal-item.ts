import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

import { MatIconModule } from '@angular/material/icon';
import { MatRippleModule } from '@angular/material/core';

export interface FoodItem{

  name:string;

  quantity:string;

  calories:number;

}

export interface Meal{

  id:string;

  name:string;

  time:string;

  icon:string;

  calories:number;

  proteins:number;

  carbs:number;

  fats:number;

  expanded:boolean;

  foods:FoodItem[];

}

@Component({

  selector:'app-meal-item',

  standalone:true,

  imports:[
    CommonModule,
    MatIconModule,
    MatRippleModule
  ],

  templateUrl:'./meal-item.html',

  styleUrl:'./meal-item.css'

})

export class MealItem{

  @Input({required:true})

  meal!:Meal;

  toggle():void{

    this.meal.expanded=!this.meal.expanded;

  }

  editMeal():void{

    console.log("Modifier repas",this.meal);

  }

  addFood():void{

    console.log("Ajouter aliment");

  }

  editFood(food:FoodItem):void{

    console.log(food);

  }

  deleteFood(food:FoodItem):void{

    this.meal.foods=this.meal.foods.filter(f=>f!==food);

  }

}