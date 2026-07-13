import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AiAgents } from './ai-agents';

describe('AiAgents', () => {
  let component: AiAgents;
  let fixture: ComponentFixture<AiAgents>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AiAgents]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AiAgents);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
