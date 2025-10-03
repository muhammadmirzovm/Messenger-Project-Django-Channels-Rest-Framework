# DCRF Messenger (Step-by-step)

## 1) Create & activate venv
```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

## 2) Install deps
```bash
pip install -r requirements.txt
```

## 3) Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## 4) Start Redis (in another terminal)
```bash
redis-server
# or: docker run -p 6379:6379 --name chat-redis -d redis:7
```

## 5) Run server
```bash
daphne -b 127.0.0.1 -p 8000 dcrf_messenger.asgi:application
```

## 6) Use the app
- Open http://127.0.0.1:8000/
- Create or join a room, then open same room in second tab to test realtime
- Click "Login" to authenticate before sending messages

## WebSocket payload examples
```json
{"action":"create","request_id":"abc123","data":{"name":"Lobby"}}
{"action":"join_room","pk":1,"request_id":"abc123","nickname":"Alice"}
{"action":"create_message","room":1,"message":"Hello!"}
{"action":"online_users","room":1}
{"action":"leave_room","pk":1}
```
