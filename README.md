# Telegram Admin Bot

Production-ready Telegram group admin bot with:

- Topic moderation modes
- Auto moderation and warnings
- DB-backed settings and whitelist persistence
- Polling mode and FastAPI webhook mode

## Quick Start

1. Install dependencies:

   pip install -e .

2. Copy env file and set your token:

   cp .env.example .env

3. Initialize DB:

   python scripts/init_db.py

4. Run polling mode:

   python scripts/start_polling.py

5. Run webhook mode:

   python scripts/start_webhook.py

## Notes

- Polling mode is ideal for local development.
- Webhook mode is ideal for production deployments.
- Topic commands must be used inside forum topics.
