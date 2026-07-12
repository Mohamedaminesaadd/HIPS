import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-feature-item',
  standalone: true,
  imports: [],
  templateUrl: './feature-item.html',
  styleUrl: './feature-item.css',
})
export class FeatureItem {
    @Input({ required: true }) title = '';
    @Input({ required: true }) description = '';

}
