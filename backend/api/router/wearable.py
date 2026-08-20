import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.events.kafka.producer import HPISKafkaProducer


router = APIRouter()

kafka_producer = HPISKafkaProducer()


@router.websocket("/ws/wearable")
async def wearable_websocket(websocket: WebSocket):

    await websocket.accept()

    print("[WS] ESP32 connected")

    try:
        while True:

            message = await websocket.receive_text()

            print("[WS] Received packet from ESP32")

            # ESP32 sends:
            # JSON:{...}
            if message.startswith("JSON:"):
                payload = message[5:]

                try:
                    data = json.loads(payload)

                    kafka_producer.publish_sensor(data)

                except json.JSONDecodeError as e:
                    print(f"[WS] Invalid JSON: {e}")

    except WebSocketDisconnect:

        print("[WS] ESP32 disconnected")

    finally:

        kafka_producer.flush()