import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';

interface AgentInsight {
  id: string;
  agent: string;
  time: string;
  message: string;
  icon: string;       // Material Symbol
  accent: 'red' | 'blue' | 'orange';
}

@Component({
  selector: 'app-agent-insights',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  templateUrl: './agent-insights.html',
  styleUrl: './agent-insights.css',
})
export class AgentInsights {
  // ── Données statiques (à brancher plus tard sur l'API / les agents IA) ──
  insights: AgentInsight[] = [
    {
      id: 'cardio',
      agent: 'Agent Cardio',
      time: '07:12',
      icon: 'monitor_heart',
      accent: 'red',
      message:
        'VFC en hausse de 8 % — le système parasympathique récupère bien. Fenêtre favorable pour une séance à haute intensité.',
    },
    {
      id: 'sommeil',
      agent: 'Agent Sommeil',
      time: '06:58',
      icon: 'bedtime',
      accent: 'blue',
      message:
        "Latence d'endormissement réduite à 9 min. Maintenir le coucher avant 22 h 30 cette semaine.",
    },
    {
      id: 'nutrition',
      agent: 'Agent Nutrition',
      time: 'Hier',
      icon: 'restaurant',
      accent: 'orange',
      message:
        'Apport protéique à 1,6 g/kg — viser 1,9 g/kg les jours de charge (+ 35 g demain).',
    },
  ];

  trackById = (_: number, item: AgentInsight) => item.id;
}