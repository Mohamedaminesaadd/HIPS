import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { Sidebar } from './components/sidebar/sidebar';
import { Header } from './components/header/header';
import { Dashboard } from "../features/dashboard/dashboard";
import { Training } from "../features/training/training";
import { Nutrition } from "../features/nutrition/nutrition";


@Component({
  selector: 'app-layout',
  standalone: true,
  templateUrl: './layout.html',
  styleUrl: './layout.css',
  imports: [
    RouterOutlet,
    Sidebar,
    Header
  ]
})
export class Layout {

  isSidebarCollapsed = false;

  toggleSidebar() {
    this.isSidebarCollapsed = !this.isSidebarCollapsed;
  }

}