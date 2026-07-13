import { Routes } from '@angular/router';
import { Login } from './login/login';
import { Sidebar } from './layout/components/sidebar/sidebar';
import { Header } from './layout/components/header/header';
import { Layout } from './layout/layout';
import { Dashboard } from './features/dashboard/dashboard';
import { PlateauAlertComponent } from './shared/plateau-alert-component/plateau-alert-component';
import {ExerciseLog} from './shared/exercise-entry/exercise-entry';

export const routes: Routes = [
      {path: 'login', component: Login},
      {path: 'sidbar', component: Sidebar},
      {path: 'header', component: Header},
      {path: 'layout', component: Layout},
      {path: 'dashboard', component: Dashboard},
      {path: 'palteauAlert',component: PlateauAlertComponent},
      {path: 'stateTraning',component:ExerciseLog}
];
