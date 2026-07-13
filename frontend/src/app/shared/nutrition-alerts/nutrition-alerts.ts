import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

import { MatIconModule } from '@angular/material/icon';

export interface NutritionAlert{

  id:number;

  title:string;

  description:string;

  level:'low'|'medium'|'high';

  icon:string;

}

@Component({

  selector:'app-nutrition-alerts',

  standalone:true,

  imports:[
    CommonModule,
    MatIconModule
  ],

  templateUrl:'./nutrition-alerts.html',

  styleUrl:'./nutrition-alerts.css'

})

export class NutritionAlerts{

  alerts:NutritionAlert[]=[

    {

      id:1,

      title:'Protéines insuffisantes',

      description:'Il manque environ 45 g de protéines pour atteindre votre objectif quotidien.',

      level:'high',

      icon:'fitness_center'

    },

    {

      id:2,

      title:'Hydratation faible',

      description:'Vous avez consommé seulement 1.8 L sur les 3 L recommandés.',

      level:'medium',

      icon:'water_drop'

    },

    {

      id:3,

      title:'Fibres alimentaires',

      description:'Augmentez votre consommation de fruits et légumes aujourd’hui.',

      level:'low',

      icon:'eco'

    }

  ];

}