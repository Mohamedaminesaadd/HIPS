import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';

import { Cardiac } from './cardiac';
import { EcgProcessingService } from '../../core/services/ecg-processing.service';
import { Esp32WebsocketService } from '../../core/services/esp32-websocket.service';
import { WearableDataService } from '../../core/services/wearable-data.service';

describe('Cardiac', () => {
  let component: Cardiac;
  let fixture: ComponentFixture<Cardiac>;

  beforeEach(async () => {
    const connected$ = new BehaviorSubject(false);
    const filteredEcg$ = new BehaviorSubject<number[]>([]);
    const heartRate$ = new BehaviorSubject<number | null>(null);
    const signalQuality$ = new BehaviorSubject<number | null>(null);
    const leadOff$ = new BehaviorSubject(false);

    await TestBed.configureTestingModule({
      imports: [Cardiac],
      providers: [
        {
          provide: Esp32WebsocketService,
          useValue: {
            connected$,
            errors$: new Subject<Event>(),
            connect: () => undefined,
          },
        },
        {
          provide: EcgProcessingService,
          useValue: { filteredEcg$, heartRate$ },
        },
        {
          provide: WearableDataService,
          useValue: { heartRate$, signalQuality$, leadOff$ },
        },
      ],
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
