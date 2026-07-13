import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Sleep } from './sleep';

describe('Sleep', () => {
  let component: Sleep;
  let fixture: ComponentFixture<Sleep>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Sleep]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Sleep);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
