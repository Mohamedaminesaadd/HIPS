import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatRippleModule } from '@angular/material/core';

@Component({
  selector: 'app-plateau-alert',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatRippleModule],
  templateUrl: './plateau-alert-component.html',
  styleUrl: './plateau-alert-component.css',
})
export class PlateauAlertComponent {
  @Input() title: string = 'Détection de plateau';
  @Input() exercise: string = 'Développé couché';
  @Input() description: string =
    "Progression stagnante depuis 3 semaines (1RM estimé : 108 → 109 kg). Suggestion de l'IA : semaine de décharge ou variation (DC haltères, pause 2 s).";
  @Input() buttonLabel: string = 'Appliquer la suggestion';

  @Output() apply = new EventEmitter<void>();

  onApply(): void {
    this.apply.emit();
  }
}