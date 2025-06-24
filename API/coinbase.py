import json
import websocket
import threading
import os
import time
from datetime import datetime, timezone

class CoinbaseStream:
    def __init__(self, url, delay):
        self.url = url
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
        os.makedirs(log_dir, exist_ok = True)
        log_path = os.path.join(log_dir, "coinbase_log.txt")

        line = f"UTC: {timestamp}    {product}: {price}    Volume: {volume}\n"
        with open(log_path, "a") as f:
            f.write(line)

        print(f"[Coinbase] Data entered at local time {datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

    def onMessage(self, _ws, response): 
        data = json.loads(response)
        if data.get("type") == "ticker":
            product = data.get("product_id", "UNKNOWN")
            price = f"{data['price']}"
            volume = data.get("last_size") or data.get("volume_24h") or "N/A"
            if price and volume:
                self.log(product, f"${price}", f"{volume}T")
    
    def onOpen(self, ws): 
        subscribe_msg = json.dumps({
            "type": "subscribe",
            "product_ids": ["BTC-USD", "ETH-USD"],    # Add more symbols here
            "channels": [
                "level2",
                "heartbeat",
                {
                    "name": "ticker", 
                    "product_ids": ["BTC-USD", "ETH-USD"]   # Add more symbols here
                }
            ]
        })
        ws.send(subscribe_msg)

    def onError(self, _ws, error):
        print(f"[Coinbase] Error: {error}")

    def onClose(self, _ws, _close_status_code, _close_msg):
        print("[Coinbase] Connection closed")

    def run(self):
        self.ws_app = websocket.WebSocketApp(
            self.url,
            on_open = self.onOpen,
            on_message = self.onMessage,
            on_error = self.onError,
            on_close = self.onClose
        )
        self.ws_app.run_forever()

    def start(self):
        self.thread = threading.Thread(target = self.run, daemon = True)
        self.thread.start()

    def stop(self):
        if self.ws_app:
            try:
                unsub = json.dumps({
                    "type": "unsubscribe",
                    "product_ids": ["BTC-USD", "ETH-USD"],    # Add more symbols here
                    "channels": [
                        "level2",
                        "heartbeat",
                        {
                            "name": "ticker", 
                            "product_ids": ["BTC-USD", "ETH-USD"]   # Add more symbols here
                        }
                    ]
                })
                self.ws_app.send(unsub)
            except Exception as e:
                print(f"[Coinbase] Error sending unsubscribe: {e}")
            self.ws_app.close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout = 5)