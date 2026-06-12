# Crypto Price Alert Bot

Real-time Bitcoin price monitoring bot that sends Telegram alerts on price movements.

## Features

- Live WebSocket connection to Binance
- Real-time BTC price tracking (updates every second)
- Configurable price change threshold (0.05% - 0.5%)
- Instant Telegram notifications
- Automatic reconnection on disconnect

## Tech Stack

- Python
- WebSocket (Binance API)
- Requests (Telegram Bot API)
- Asynchronous real-time processing

## How It Works

1. Connects to Binance WebSocket stream
2. Subscribes to BTC-USDT bookTicker for real-time bid/ask
3. Calculates mid-price every second
4. Compares with previous price
5. Sends Telegram alert when price change exceeds threshold

## Setup

1. Clone repository
2. Install dependencies:
   ```bash
   pip install websocket-client requests
