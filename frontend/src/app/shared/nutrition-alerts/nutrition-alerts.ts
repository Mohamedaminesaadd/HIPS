import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';

export type AlertLevel = 'low' | 'medium' | 'high';

export interface NutritionAlert {
  id: number;
  title: string;
  description: string;
  level: AlertLevel;
  icon: string;
  current: number;        // valeur actuelle
  target: number;         // objectif
  unit: string;           // 'g', 'L', ...
  action: string;         // libellé du bouton d'action
}

@Component({
  selector: 'app-nutrition-alerts',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  templateUrl: './nutrition-alerts.html',
  styleUrl: './nutrition-alerts.css',
})
export class NutritionAlerts {
  alerts: NutritionAlert[] = [
    {
      id: 1,
      title: 'Protéines insuffisantes',
      description: 'Il manque environ 45 g de protéines pour atteindre votre objectif quotidien.',
      level: 'high',
      icon: 'fitness_center',
      current: 120,
      target: 165,
      unit: 'g',
      action: 'Suggérer une source',
    },
    {
      id: 2,
      title: 'Hydratation faible',
      description: 'Vous avez consommé seulement 1,8 L sur les 3 L recommandés.',
      level: 'medium',
      icon: 'water_drop',
      current: 1.8,
      target: 3,
      unit: 'L',
      action: 'Ajouter un verre',
    },
    {
      id: 3,
      title: 'Fibres alimentaires',
      description: 'Augmentez votre consommation de fruits et légumes aujourd\'hui.',
      level: 'low',
      icon: 'eco',
      current: 18,
      target: 30,
      unit: 'g',
      action: 'Voir des idées',
    },
  ];

  // ── Libellé FR du niveau ──
  levelLabel(level: AlertLevel): string {
    switch (level) {
      case 'high':   return 'Critique';
      case 'medium': return 'Modéré';
      case 'low':    return 'Léger';
    }
  }

  // ── Mappe le niveau vers la classe de sévérité CSS ──
  severity(level: AlertLevel): 'danger' | 'warning' | 'success' {
    switch (level) {
      case 'high':   return 'danger';
      case 'medium': return 'warning';
      case 'low':    return 'success';
    }
  }

  // ── Pourcentage de progression (borné 0–100) ──
  percent(alert: NutritionAlert): number {
    if (alert.target <= 0) return 0;
    return Math.min(100, Math.max(0, (alert.current / alert.target) * 100));
  }

  onAction(alert: NutritionAlert): void {
    // TODO : brancher sur l'Agent Nutrition (IA)
    console.log('Action carence →', alert.title);
  }
}