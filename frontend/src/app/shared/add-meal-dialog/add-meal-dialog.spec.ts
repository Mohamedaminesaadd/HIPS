import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddMealDialog } from './add-meal-dialog';

describe('AddMealDialog', () => {
  let component: AddMealDialog;
  let fixture: ComponentFixture<AddMealDialog>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddMealDialog]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AddMealDialog);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
