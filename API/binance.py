import json
import websocket
import threading
import os
import time
from datetime import datetime, timezone

class BinanceStream: 
    def __init__(self, primary_url, backup_url, delay):
        self.primary_url = primary_url
        self.backup_url = backup_url
        self.delay = delay
        self.ws_app = None
        self.thread = None
        self.last_log_time = 0

    # Change this fucntion entirely to work with SQL
    def log(self, product, price, volume): 
        now = time.time()
        if now - self.last_log_time < self.delay:
            return
        self.last_log_time = now

        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3]
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "binance_log.txt")

        line = f"UTC: {timestamp}    {product}: {price}    Volume: {volume}\n"
        with open(log_path, "a") as f:
            f.write(line)

        print(f"[Binance]  Data entered at local time {datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

    def onMessage(self, _ws, response): 
        data = json.loads(response)
        symbol = data.get('s', '').upper()
        if 'p' in data and 'q' in data:
            price = f"${data['p']}"
            volume = f"{data['q']}"
            self.log(symbol, price, volume)

    def onOpen(self, ws): 
        ws.send(json.dumps({
            "method": "SUBSCRIBE",
            "params": ["btcusdt@trade", "ethusdt@trade"],    # Add more symbols here
            "id": 1
        }))

    def onError(self, _ws, error):
        print(f"[Binance] Error: {error}")

    def onClose(self, _ws, _close_status_code, _close_msg):
        print("[Binance] Connection closed")

    def run(self, url):
        self.ws_app = websocket.WebSocketApp(
            url + "/ws",
            on_open = self.onOpen,
            on_message = self.onMessage,
            on_error = self.onError,
            on_close = self.onClose
        )
        self.ws_app.run_forever()

    def start(self):
        def target():
            try: 
                self.run(self.primary_url)
            except Exception as e:
                print(f"[Binance] Primary failed: {e}")
                if self.backup_url:
                    self.run(self.backup_url)
        self.thread = threading.Thread(target = target, daemon = True)
        self.thread.start()

    def stop(self):
        if self.ws_app:
            try:
                unsub = json.dumps({
                    "method": "UNSUBSCRIBE",
                    "params": ["btcusdt@trade", "ethusdt@trade"],    # Add more symbols here
                    "id": 2
                })
                self.ws_app.send(unsub)
            except Exception as e:
                print(f"[Binance] Error sending unsubscribe: {e}")
            self.ws_app.close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout = 5)