import { Routes } from '@angular/router';
import { Login } from './login/login';
import { Sidebar } from './layout/components/sidebar/sidebar';
import { Header } from './layout/components/header/header';
import { Layout } from './layout/layout';
import { Dashboard } from './features/dashboard/dashboard';
import { PlateauAlertComponent } from './shared/plateau-alert-component/plateau-alert-component';
import {ExerciseLog} from './shared/exercise-entry/exercise-entry';
import { NutritionHeader } from './shared/nutrition-header/nutrition-header';
import { NutritionStats } from './shared/nutrition-stats/nutrition-stats';
import { MealLog } from './shared/meal-log/meal-log';
import { NutritionAlerts } from './shared/nutrition-alerts/nutrition-alerts';
import { Nutrition } from './features/nutrition/nutrition';

export const routes: Routes = [
      {path: 'login', component: Login},
      {path: 'sidbar', component: Sidebar},
      {path: 'header', component: Header},
      {path: 'layout', component: Layout},
      {path: 'dashboard', component: Dashboard},
      {path: 'palteauAlert',component: PlateauAlertComponent},
      {path: 'stateTraning',component:ExerciseLog},
      {path: 'test',component:Nutrition }
];
