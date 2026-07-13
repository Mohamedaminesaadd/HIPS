import { Routes } from '@angular/router';
import { Login } from './login/login';
import { Sidebar } from './layout/components/sidebar/sidebar';
import { Header } from './layout/components/header/header';
import { Layout } from './layout/layout';

export const routes: Routes = [
      {path: 'login', component: Login},
      {path: 'sidbar', component: Sidebar},
      {path: 'header', component: Header},
      {path: 'layout', component: Layout},
];
