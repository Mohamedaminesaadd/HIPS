import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PlateauAlertComponent } from './plateau-alert-component';

describe('PlateauAlertComponent', () => {
  let component: PlateauAlertComponent;
  let fixture: ComponentFixture<PlateauAlertComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PlateauAlertComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PlateauAlertComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
