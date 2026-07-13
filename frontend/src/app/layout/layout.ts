import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { Sidebar } from './components/sidebar/sidebar';
import { Header } from './components/header/header';

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

  toggleSidebar(): void {

    this.isSidebarCollapsed = !this.isSidebarCollapsed;

  }

}