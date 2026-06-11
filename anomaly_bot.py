import websocket
import json
import numpy as np
from collections import deque
from sklearn.ensemble import IsolationForest
import requests
import time
from datetime import datetime

# ==================== CONFIGURATION ====================
# Telegram Bot (REPLACE WITH YOURS)
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Get from @BotFather
CHAT_ID = "YOUR_CHAT_ID"  # Get from /getUpdates

# Groq API (REPLACE WITH YOUR KEY)
GROQ_API_KEY = "gsk_YOUR_GROQ_API_KEY"

# Anomaly detection settings
SPREAD_HISTORY = 100  # How many past spreads to remember
ANOMALY_THRESHOLD = 0.1  # 10% of points flagged as anomalies
# =======================================================

# Global storage for spreads
spreads = deque(maxlen=SPREAD_HISTORY)
model = IsolationForest(contamination=ANOMALY_THRESHOLD, random_state=42)

def detect_anomaly(bid, ask):
    """Returns (is_anomaly, spread)"""
    spread = ask - bid
    spreads.append([spread])
    
    if len(spreads) >= 50:  # Need enough data
        preds = model.fit_predict(list(spreads))
        if preds[-1] == -1:
            return True, spread
    return False, spread

def send_telegram_alert(message):
    """Send alert to your Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_ai_explanation(bid, ask, spread):
    """Get AI explanation using Groq"""
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = f"""A sudden anomaly was detected in the BTC-USDT order book:

Current bid price: {bid}
Current ask price: {ask}
Current spread: {spread}

This spread is significantly wider than normal. In 1-2 sentences, explain what this might indicate to a crypto trader (e.g., sell wall, buy pressure, manipulation, etc.). Keep it under 50 words."""
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI explanation failed: {e}"

def on_message(ws, message):
    """Handle incoming WebSocket messages"""
    try:
        data = json.loads(message)
        
        # Extract best bid and ask
        best_bid = float(data['b'][0]) if data.get('b') else None
        best_ask = float(data['a'][0]) if data.get('a') else None
        
        if best_bid and best_ask:
            is_anomaly, spread = detect_anomaly(best_bid, best_ask)
            
            if is_anomaly:
                print(f"\n🚨 ANOMALY DETECTED at {datetime.now()}")
                print(f"Bid: {best_bid}, Ask: {best_ask}, Spread: {spread}")
                
                # Get AI explanation
                explanation = get_ai_explanation(best_bid, best_ask, spread)
                print(f"AI: {explanation}")
                
                # Send Telegram alert
                alert_msg = f"""🚨 *Crypto Anomaly Alert*
Time: {datetime.now().strftime('%H:%M:%S UTC')}
Bid: {best_bid}
Ask: {best_ask}
Spread: {spread}

🤖 *AI Analysis:* {explanation}"""
                send_telegram_alert(alert_msg)
                
    except Exception as e:
        print(f"Error processing message: {e}")

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection closed. Reconnecting in 5 seconds...")
    time.sleep(5)
    start_websocket()

def on_open(ws):
    print("Connected to Binance WebSocket")
    subscribe_msg = {
        "method": "SUBSCRIBE",
        "params": ["btcusdt@depth10@100ms"],
        "id": 1
    }
    ws.send(json.dumps(subscribe_msg))
    print("Subscribed to BTC-USDT order book")

def start_websocket():
    ws = websocket.WebSocketApp(
        "wss://stream.binance.com:9443/ws",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

if __name__ == "__main__":
    print("Starting Crypto Anomaly Detection Bot...")
    print(f"Telegram alerts: {'ON' if TELEGRAM_TOKEN != 'YOUR_TELEGRAM_BOT_TOKEN' else 'OFF (configure first)'}")
    start_websocket()