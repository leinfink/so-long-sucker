import redis
import pickle
from django.conf import settings

def get_game_through_redis(game_id):
    if settings.REDIS_UNIX:
         r = redis.Redis(unix_socket_path=settings.REDIS_UNIX_PATH, db=0)
    else:
        r = redis.Redis(host=settings.REDIS_HOST, port=6379, db=0)
    return(pickle.loads(r.get('game_'+str(game_id))))
