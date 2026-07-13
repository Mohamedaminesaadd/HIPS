import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ExerciseEntry } from './exercise-entry';

describe('ExerciseEntry', () => {
  let component: ExerciseEntry;
  let fixture: ComponentFixture<ExerciseEntry>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ExerciseEntry]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ExerciseEntry);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
