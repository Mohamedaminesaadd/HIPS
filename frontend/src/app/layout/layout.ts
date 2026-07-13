import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { Sidebar } from './components/sidebar/sidebar';
import { Header } from './components/header/header';
import { Dashboard } from "../features/dashboard/dashboard";
import { Training } from "../features/training/training";

@Component({
  selector: 'app-layout',
  standalone: true,
  templateUrl: './layout.html',
  styleUrl: './layout.css',
  imports: [
    RouterOutlet,
    Sidebar,
    Header,
    Dashboard,
    Training
]
})
export class Layout {

  isSidebarCollapsed = false;

  toggleSidebar(): void {

    this.isSidebarCollapsed = !this.isSidebarCollapsed;

  }

}