import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NutritionAlerts } from './nutrition-alerts';

describe('NutritionAlerts', () => {
  let component: NutritionAlerts;
  let fixture: ComponentFixture<NutritionAlerts>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NutritionAlerts]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NutritionAlerts);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
