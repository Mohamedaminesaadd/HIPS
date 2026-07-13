import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AgentInsights } from './agent-insights';

describe('AgentInsights', () => {
  let component: AgentInsights;
  let fixture: ComponentFixture<AgentInsights>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AgentInsights]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AgentInsights);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
