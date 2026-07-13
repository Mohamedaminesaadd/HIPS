import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-nutrition-header',
  standalone: true,
  imports: [
    CommonModule,
    MatIconModule,
    MatButtonModule
  ],
  templateUrl: './nutrition-header.html',
  styleUrl: './nutrition-header.css'
})
export class NutritionHeader {

  @Output()
  addMeal = new EventEmitter<void>();

  @Output()
  previousDay = new EventEmitter<void>();

  @Output()
  nextDay = new EventEmitter<void>();

  today = new Date();

  get currentDate(): string {

    return this.today.toLocaleDateString('fr-FR', {

      weekday: 'short',

      day: 'numeric',

      month: 'short',

      year: 'numeric'

    });

  }

}