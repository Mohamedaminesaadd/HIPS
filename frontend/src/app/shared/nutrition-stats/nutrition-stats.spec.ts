import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NutritionStats } from './nutrition-stats';

describe('NutritionStats', () => {
  let component: NutritionStats;
  let fixture: ComponentFixture<NutritionStats>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NutritionStats]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NutritionStats);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
