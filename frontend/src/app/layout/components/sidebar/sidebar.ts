import { Component, HostBinding } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatRippleModule } from '@angular/material/core';
import { RouterLink, RouterLinkActive, Router } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  templateUrl: './sidebar.html',
  styleUrls: ['./sidebar.css'],
  imports: [
    MatIconModule,
    MatRippleModule,
    RouterLink,
    RouterLinkActive
  ],
})
export class Sidebar {

  isCollapsed = false;

  constructor(private router: Router) {}

  @HostBinding('class.collapsed')
  get collapsed(): boolean {
    return this.isCollapsed;
  }

  toggleSidebar(): void {
    this.isCollapsed = !this.isCollapsed;
  }

  logout(): void {
    // this.auth.logout();
    this.router.navigate(['/login']);
  }
}