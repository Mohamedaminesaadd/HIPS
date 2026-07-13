import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StatsRowTraining } from './stats-row-training';

describe('StatsRowTraining', () => {
  let component: StatsRowTraining;
  let fixture: ComponentFixture<StatsRowTraining>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StatsRowTraining]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StatsRowTraining);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
