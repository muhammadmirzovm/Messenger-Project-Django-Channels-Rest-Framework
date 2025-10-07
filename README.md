# DCRF Messenger

Realtime group chat built with **Django**, **Channels**, **DCRF (Django Channels REST Framework)**, and **Redis**.

- Telegram-style UI (light/dark)
- Day dividers: **Today / Yesterday / 03 Oct 2025**
- Live **online users** (global + per-room) with counts
- Mobile: **Users (N)** button opens a slide-in panel (right/left), backdrop + ✕ close
- Immediate timestamps on new messages (no refresh)

---

## 0) Prerequisites

- Python 3.11+ (3.12/3.13 OK)
- Redis 6/7+ running at `127.0.0.1:6379`

---

## 1) Setup

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
