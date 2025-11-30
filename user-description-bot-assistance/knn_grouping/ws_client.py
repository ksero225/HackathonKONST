# knn_grouping/ws_client.py
import json
import threading
import time
from typing import List

import websocket  # type: ignore


def stomp_frame(command, headers=None, body: str = "") -> str:
    if headers is None:
        headers = {}
    frame = command + "\n"
    for key, value in headers.items():
        frame += f"{key}:{value}\n"
    frame += "\n" + body + "\0"
    return frame


class GroupsWebSocketClient:
    """
    Prosty klient WS/STOMP tylko do:
    - CONNECT
    - SUBSCRIBE na /topic/groups (podgląd odpowiedzi)
    - SEND na /app/groups  (trafia w @MessageMapping("/groups"))
    """

    def __init__(self, uri: str):
        self.uri = uri
        self.ws = None
        self.connected = False

    def connect(self):
        def _run():
            self.ws = websocket.WebSocketApp(
                self.uri,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
            )
            self.ws.run_forever()

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        time.sleep(1.5)

    def on_open(self, ws):
        print("✅ [WS-GROUPS] Połączono z serwerem.")
        self.connected = True

        connect_frame = stomp_frame(
            "CONNECT",
            headers={
                "accept-version": "1.1,1.2",
                "host": "localhost",
            },
        )
        ws.send(connect_frame)
        time.sleep(0.3)

        sub_frame = stomp_frame(
            "SUBSCRIBE",
            headers={
                "id": "sub-groups-0",
                "destination": "/topic/groups",
            },
        )
        ws.send(sub_frame)
        print("🎧 [WS-GROUPS] Zasubskrybowano /topic/groups")

    def on_message(self, ws, message):
        if message == "\n":
            return

        if "\n\n" in message:
            header, body = message.split("\n\n", 1)
            clean_body = body.replace("\x00", "").strip()
            if clean_body:
                print(f"📩 [WS-GROUPS ODBIÓR]: {clean_body[:200]}...")

    def on_error(self, ws, error):
        print(f"❌ [WS-GROUPS] Błąd: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("🔌 [WS-GROUPS] Rozłączono.")
        self.connected = False

    def send_groups(self, groups_payload: List[dict]):
        if not self.ws or not self.connected:
            print("⚠️ [WS-GROUPS] Brak połączenia – nie wysyłam.")
            return

        try:
            body = json.dumps(groups_payload, ensure_ascii=False)
            body_bytes = body.encode("utf-8")

            send_frame = stomp_frame(
                "SEND",
                headers={
                    "destination": "/app/groups",
                    "content-type": "application/json;charset=UTF-8",
                    "content-length": str(len(body_bytes)),
                },
                body=body,
            )

            print(f"[WS-GROUPS] STOMP SEND frame body (skrót): {body[:200]}...")
            self.ws.send(send_frame)
            print(f"📤 [WS-GROUPS WYSŁANO] {len(groups_payload)} grup.")
        except Exception as e:
            print(f"❌ [WS-GROUPS] Błąd wysyłania: {e}")
