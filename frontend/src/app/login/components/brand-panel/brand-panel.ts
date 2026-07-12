import { Component } from '@angular/core';
import { FeatureItem } from '../feature-item/feature-item';   

@Component({
  selector: 'app-brand-panel',
  standalone: true,
  imports: [FeatureItem],
  templateUrl: './brand-panel.html',
  styleUrl: './brand-panel.css',
})
export class BrandPanel {

}
