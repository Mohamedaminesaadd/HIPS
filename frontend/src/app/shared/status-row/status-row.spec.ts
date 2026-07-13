import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StatusRow } from './status-row';

describe('StatusRow', () => {
  let component: StatusRow;
  let fixture: ComponentFixture<StatusRow>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StatusRow]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StatusRow);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
