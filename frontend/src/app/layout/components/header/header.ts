import {
  Component,
  Output,
  EventEmitter,
  OnInit,
  ChangeDetectionStrategy,
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatBadgeModule } from '@angular/material/badge';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatRippleModule } from '@angular/material/core';

@Component({
  selector: 'app-header',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    MatIconModule,
    MatBadgeModule,
    MatTooltipModule,
    MatRippleModule,
  ],
  templateUrl: './header.html',
  styleUrl: './header.css',
})
export class Header implements OnInit {

  @Output()
  toggleSidebar = new EventEmitter<void>();

  // ==========================
  // Informations utilisateur
  // ==========================

  userName = 'Mohamed Amine';
  userRole = 'Athlète';
  userInitials = 'MA';

  // ==========================
  // Notifications
  // ==========================

  notifCount = 3;

  // ==========================
  // Bracelet HPIS
  // ==========================

  wearableConnected = true;
  wearableBattery = 87;

  // ==========================
  // Chargement
  // ==========================

  isLoading = false;

  ngOnInit(): void {}

  get today(): string {
    return new Date().toLocaleDateString('fr-FR', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  }

  toggle(): void {
    this.toggleSidebar.emit();
  }
}