import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NutritionCard } from './nutrition-card';

describe('NutritionCard', () => {
  let component: NutritionCard;
  let fixture: ComponentFixture<NutritionCard>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NutritionCard]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NutritionCard);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
