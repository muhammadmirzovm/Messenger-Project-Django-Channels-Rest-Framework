from typing import List, Set
from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.redis import RedisCache

TTL = getattr(settings, "PRESENCE_TTL_SECONDS", 60)

def _user_ttl_key(user_id: int) -> str:
    return f"presence:user:{user_id}"  

def _global_set_key() -> str:
    return "presence:global:users"

def _room_set_key(room_id: int) -> str:
    return f"presence:room:{room_id}:users"

def _client():
    try:
        return cache.client.get_client()
    except AttributeError:
        raise RuntimeError("Presence requires RedisCache backend.")


def sadd(key: str, member):
    _client().sadd(key, member)

def srem(key: str, member):
    _client().srem(key, member)

def smembers(key: str):
    return _client().smembers(key)

def heartbeat(user_id: int) -> None:
    cache.set(_user_ttl_key(user_id), "1", TTL)
    sadd(_global_set_key(), user_id)

def remove_global(user_id: int) -> None:
    cache.delete(_user_ttl_key(user_id))
    srem(_global_set_key(), user_id)

def list_online_user_ids() -> List[int]:
    raw = smembers(_global_set_key())
    alive: List[int] = []
    for uid_raw in raw:
        try:
            uid = int(uid_raw)
        except Exception:
            uid = uid_raw
        if cache.get(_user_ttl_key(uid)) is not None:
            alive.append(uid)
        else:
            srem(_global_set_key(), uid) 
    return alive

def room_join(user_id: int, room_id: int) -> None:
    sadd(_room_set_key(room_id), user_id)
    heartbeat(user_id)

def room_leave(user_id: int, room_id: int) -> None:
    srem(_room_set_key(room_id), user_id)

def room_online_user_ids(room_id: int) -> List[int]:
    raw = smembers(_room_set_key(room_id))
    alive: List[int] = []
    for uid_raw in raw:
        try:
            uid = int(uid_raw)
        except Exception:
            uid = uid_raw
        if cache.get(_user_ttl_key(uid)) is not None:
            alive.append(uid)
        else:
            srem(_room_set_key(room_id), uid)
    return alive
