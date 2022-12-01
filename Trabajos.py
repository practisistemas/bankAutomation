import os
import redis
from dotenv import load_dotenv

load_dotenv()
def cola_de_trabajo (id_transaccion):
    r = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'),db=0, charset='utf-8')
    r.lpush("Data"+id_transaccion, id_transaccion)