import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';

import { WearablePacket } from '../models/wearable-data.model';

@Injectable({
  providedIn: 'root'
})
export class Esp32WebsocketService implements OnDestroy {

  // ============================================================
  // CONFIGURATION
  // ============================================================

  /**
   * Temporary ESP32 address.
   *
   * Later we will replace this with automatic ESP32 discovery.
   */
  private readonly defaultUrl = 'ws://10.42.0.71/ws';

  // ============================================================
  // WEBSOCKET
  // ============================================================

  private socket: WebSocket | null = null;

  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  private shouldReconnect = true;

  private reconnectAttempts = 0;

  private readonly maxReconnectDelay = 10000;

  // ============================================================
  // CONNECTION STATE
  // ============================================================

  private readonly connectedSubject =
    new BehaviorSubject<boolean>(false);

  readonly connected$: Observable<boolean> =
    this.connectedSubject.asObservable();

  // ============================================================
  // RAW MESSAGES
  // ============================================================

  private readonly messageSubject =
    new Subject<string>();

  readonly messages$: Observable<string> =
    this.messageSubject.asObservable();

  // ============================================================
  // ECG CHUNKS
  // ============================================================

  private readonly ecgSubject =
    new Subject<number[]>();

  /**
   * Emits ECG chunks received from the ESP32.
   *
   * ESP32 sends:
   *
   * ECG:2048,2050,2051,...
   */
  readonly ecg$: Observable<number[]> =
    this.ecgSubject.asObservable();

  // ============================================================
  // COMPLETE WEARABLE PACKETS
  // ============================================================

  private readonly jsonSubject =
    new Subject<WearablePacket>();

  /**
   * Emits complete JSON packets received from ESP32.
   */
  readonly jsonPackets$: Observable<WearablePacket> =
    this.jsonSubject.asObservable();

  // ============================================================
  // ERRORS
  // ============================================================

  private readonly errorSubject =
    new Subject<Event>();

  readonly errors$: Observable<Event> =
    this.errorSubject.asObservable();

  // ============================================================
  // CONNECT
  // ============================================================

  connect(url: string = this.defaultUrl): void {

    // ----------------------------------------------------------
    // SSR protection
    // ----------------------------------------------------------

    if (typeof window === 'undefined') {

      console.warn(
        '[ESP32] WebSocket unavailable during SSR.'
      );

      return;
    }

    // ----------------------------------------------------------
    // Already connected / connecting
    // ----------------------------------------------------------

    if (
      this.socket &&
      (
        this.socket.readyState === WebSocket.OPEN ||
        this.socket.readyState === WebSocket.CONNECTING
      )
    ) {

      console.log(
        '[ESP32] Already connected or connecting.'
      );

      return;
    }

    this.shouldReconnect = true;

    console.log(
      `[ESP32] Connecting to ${url}...`
    );

    try {

      this.socket = new WebSocket(url);

      // ========================================================
      // CONNECTION OPENED
      // ========================================================

      this.socket.onopen = () => {

        console.log(
          `[ESP32] Connected to ${url}`
        );

        this.connectedSubject.next(true);

        this.reconnectAttempts = 0;
      };

      // ========================================================
      // MESSAGE RECEIVED
      // ========================================================

      this.socket.onmessage = (event: MessageEvent) => {

        this.handleMessage(event.data);
      };

      // ========================================================
      // ERROR
      // ========================================================

      this.socket.onerror = (event: Event) => {

        console.error(
          '[ESP32] WebSocket error:',
          event
        );

        this.errorSubject.next(event);
      };

      // ========================================================
      // CONNECTION CLOSED
      // ========================================================

      this.socket.onclose = (event: CloseEvent) => {

        console.warn(
          `[ESP32] Connection closed. Code=${event.code}`
        );

        this.connectedSubject.next(false);

        this.socket = null;

        // Automatic reconnection
        if (this.shouldReconnect) {

          this.scheduleReconnect(url);
        }
      };

    } catch (error) {

      console.error(
        '[ESP32] Connection failed:',
        error
      );

      this.connectedSubject.next(false);

      this.scheduleReconnect(url);
    }
  }

  // ============================================================
  // MESSAGE ROUTER
  // ============================================================

  private handleMessage(message: unknown): void {

    // ----------------------------------------------------------
    // Make sure the message is a string
    // ----------------------------------------------------------

    if (typeof message !== 'string') {

      console.warn(
        '[ESP32] Received non-string message.'
      );

      return;
    }

    // Publish raw message
    this.messageSubject.next(message);

    // ==========================================================
    // ECG MESSAGE
    // ==========================================================

    if (message.startsWith('ECG:')) {

      this.handleEcgMessage(message);

      return;
    }

    // ==========================================================
    // JSON MESSAGE
    // ==========================================================

    if (message.startsWith('JSON:')) {

      this.handleJsonMessage(message);

      return;
    }

    // ==========================================================
    // UNKNOWN MESSAGE
    // ==========================================================

    console.warn(
      '[ESP32] Unknown message:',
      message
    );
  }

  // ============================================================
  // ECG MESSAGE PARSER
  // ============================================================

  private handleEcgMessage(message: string): void {

    try {

      /**
       * Remove "ECG:"
       *
       * ECG:2048,2050,2051
       *
       * becomes:
       *
       * 2048,2050,2051
       */

      const payload = message.substring(4);

      if (!payload.trim()) {

        return;
      }

      const samples = payload
        .split(',')
        .map(value => Number(value.trim()))
        .filter(value => Number.isFinite(value));

      if (samples.length === 0) {

        console.warn(
          '[ESP32] Empty ECG packet.'
        );

        return;
      }

      // Send ECG samples to subscribers
      this.ecgSubject.next(samples);

    } catch (error) {

      console.error(
        '[ESP32] ECG parsing error:',
        error
      );
    }
  }

  // ============================================================
  // JSON MESSAGE PARSER
  // ============================================================

  private handleJsonMessage(message: string): void {

    try {

      /**
       * Remove "JSON:"
       */

      const payload = message.substring(5);

      if (!payload.trim()) {

        return;
      }

      const packet =
        JSON.parse(payload) as WearablePacket;

      // Send packet to subscribers
      this.jsonSubject.next(packet);

    } catch (error) {

      console.error(
        '[ESP32] JSON parsing error:',
        error
      );

      console.error(
        '[ESP32] Invalid message:',
        message
      );
    }
  }

  // ============================================================
  // SEND MESSAGE TO ESP32
  // ============================================================

  send(message: string): boolean {

    if (
      !this.socket ||
      this.socket.readyState !== WebSocket.OPEN
    ) {

      console.warn(
        '[ESP32] Cannot send message.'
      );

      return false;
    }

    this.socket.send(message);

    return true;
  }

  // ============================================================
  // DISCONNECT
  // ============================================================

  disconnect(): void {

    console.log(
      '[ESP32] Manual disconnect.'
    );

    this.shouldReconnect = false;

    this.clearReconnectTimer();

    if (this.socket) {

      this.socket.close();

      this.socket = null;
    }

    this.connectedSubject.next(false);
  }

  // ============================================================
  // AUTOMATIC RECONNECTION
  // ============================================================

  private scheduleReconnect(url: string): void {

    if (!this.shouldReconnect) {

      return;
    }

    this.clearReconnectTimer();

    this.reconnectAttempts++;

    /**
     * Exponential backoff:
     *
     * 1 second
     * 2 seconds
     * 4 seconds
     * 8 seconds
     * 10 seconds maximum
     */

    const delay = Math.min(
      1000 *
      Math.pow(
        2,
        this.reconnectAttempts - 1
      ),
      this.maxReconnectDelay
    );

    console.log(
      `[ESP32] Reconnecting in ${delay} ms...`
    );

    this.reconnectTimer = setTimeout(() => {

      this.connect(url);

    }, delay);
  }

  // ============================================================
  // CLEAR RECONNECT TIMER
  // ============================================================

  private clearReconnectTimer(): void {

    if (this.reconnectTimer !== null) {

      clearTimeout(this.reconnectTimer);

      this.reconnectTimer = null;
    }
  }

  // ============================================================
  // CONNECTION STATUS
  // ============================================================

  isConnected(): boolean {

    return (
      this.socket !== null &&
      this.socket.readyState === WebSocket.OPEN
    );
  }

  // ============================================================
  // CLEANUP
  // ============================================================

  ngOnDestroy(): void {

    this.disconnect();

    this.connectedSubject.complete();

    this.messageSubject.complete();

    this.ecgSubject.complete();

    this.jsonSubject.complete();

    this.errorSubject.complete();
  }
}