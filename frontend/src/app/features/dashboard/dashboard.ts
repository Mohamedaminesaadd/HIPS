import { Component } from '@angular/core';
import { StatsRow } from "../../shared/status-row/status-row";
import { AgentInsights } from "../../shared/agent-insights/agent-insights";
import { VfcChart } from "../../shared/tendance-vfc/tendance-vfc";
import { NutritionCardComponent } from "../../shared/nutrition-card/nutrition-card";

@Component({
  selector: 'app-dashboard',
  imports: [StatsRow, AgentInsights, VfcChart, NutritionCardComponent],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard {

}
