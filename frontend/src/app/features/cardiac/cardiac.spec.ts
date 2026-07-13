import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Cardiac } from './cardiac';

describe('Cardiac', () => {
  let component: Cardiac;
  let fixture: ComponentFixture<Cardiac>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Cardiac]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Cardiac);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
