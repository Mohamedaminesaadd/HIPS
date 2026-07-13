import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NutritionHeader } from './nutrition-header';

describe('NutritionHeader', () => {
  let component: NutritionHeader;
  let fixture: ComponentFixture<NutritionHeader>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NutritionHeader]
    })
    .compileComponents();

    fixture = TestBed.createComponent(NutritionHeader);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
