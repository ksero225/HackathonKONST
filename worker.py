import websocket
import threading
import time
import json
import os
import requests
from dotenv import load_dotenv

from venue_manager import venue_manager

load_dotenv()

WS_URI = os.getenv("WS_URI")
JAVA_API_URL = os.getenv("JAVA_API_URL")

if not WS_URI or not JAVA_API_URL:
    print(" ERROR: Missing WS_URI or JAVA_API_URL in .env")
    exit(1)

def stomp_frame(command, headers=None, body=""):
    if headers is None: headers = {}
    frame = command + "\n"
    for key, value in headers.items():
        frame += f"{key}:{value}\n"
    frame += "\n" + body + "\0"
    return frame

class RadarWorker:
    def __init__(self):
        self.uri = WS_URI
        self.ws = None
        self.connected = False
        self.running = True
        self.processed_group_ids = set()
        
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True

    def start(self):
        self.thread.start()
        print(f" [WORKER] Starting... Connecting to {self.uri}")

    def _run_loop(self):
        while self.running:
            try:
                self.ws = websocket.WebSocketApp(
                    self.uri,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close
                )
                self.ws.run_forever()
            except Exception as e:
                print(f" [WS] Connection error: {e}")
                time.sleep(3)
            
            if self.running:
                print(" [WS] Reconnecting in 3s...")
                time.sleep(3)

    def on_open(self, ws):
        print(" [WS] Connected.")
        self.connected = True
        ws.send(stomp_frame("CONNECT", headers={"accept-version":"1.1,1.2", "host":"localhost"}))
        time.sleep(0.5)
        ws.send(stomp_frame("SUBSCRIBE", headers={"id":"sub-0", "destination":"/topic/groups"}))

    def on_message(self, ws, message):
        if "\n\n" not in message: return
        body = message.split("\n\n", 1)[1].strip().replace('\x00', '')
        if not body: return
        
        threading.Thread(target=self.process_incoming_data, args=(body,)).start()

    def process_incoming_data(self, json_body):
        try:
            data = json.loads(json_body)
            groups = data if isinstance(data, list) else [data]

            for group in groups:
                g_id = group.get('groupId')

                if g_id in self.processed_group_ids:
                    continue

                print(f"\n [WORKER] Processing Group ID: {g_id}")

                lat = group.get('latitude')
                lng = group.get('longitude')
                traits = group.get('topTraits', [])
                user_ids = group.get('users', [])

                if lat is None or lng is None:
                    print(" Skipping group without location.")
                    continue

                category_str = ", ".join(traits) if traits else "meeting"
                
                venue_result = venue_manager.find_venue(lat, lng, category_str)

                full_description = f"{venue_result['name']} ({venue_result.get('address','')}). {venue_result.get('description', '')}"
                
                final_lat = venue_result.get('lat', lat)
                final_lng = venue_result.get('lng', lng)

                payload = {
                    "eventId": g_id,
                    "userIds": user_ids,
                    "description": full_description,
                    "latitude": final_lat,
                    "longitude": final_lng
                }

                self.send_to_java(payload)
                
                self.processed_group_ids.add(g_id)

        except Exception as e:
            print(f" [LOGIC] Error processing message: {e}")

    def send_to_java(self, payload):
        try:
            print(f" [HTTP] Sending Event {payload['eventId']} to Java...")
            res = requests.post(JAVA_API_URL, json=payload, timeout=5)
            
            if res.status_code in [200, 201]:
                print(f" [HTTP] Success! (200 OK)")
            else:
                print(f" [HTTP] Java Error: {res.status_code} - {res.text}")
        except Exception as e:
            print(f" [HTTP] Connection failed: {e}")

    def on_error(self, ws, error): print(f" [WS] Error: {error}")
    def on_close(self, ws, *args): 
        print(" [WS] Disconnected.")
        self.connected = False

if __name__ == "__main__":
    worker = RadarWorker()
    worker.start()
    
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping worker...")