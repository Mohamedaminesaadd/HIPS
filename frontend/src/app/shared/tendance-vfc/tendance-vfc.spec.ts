import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TendanceVFC } from './tendance-vfc';

describe('TendanceVFC', () => {
  let component: TendanceVFC;
  let fixture: ComponentFixture<TendanceVFC>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TendanceVFC]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TendanceVFC);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
