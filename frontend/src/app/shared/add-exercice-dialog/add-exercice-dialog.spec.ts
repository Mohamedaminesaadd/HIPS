import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddExerciceDialog } from './add-exercice-dialog';

describe('AddExerciceDialog', () => {
  let component: AddExerciceDialog;
  let fixture: ComponentFixture<AddExerciceDialog>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddExerciceDialog]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AddExerciceDialog);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
