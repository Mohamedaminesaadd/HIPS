import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MealLog } from './meal-log';

describe('MealLog', () => {
  let component: MealLog;
  let fixture: ComponentFixture<MealLog>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MealLog]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MealLog);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
