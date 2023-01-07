import os
import redis
from dotenv import load_dotenv

load_dotenv()
def cola_de_trabajo (id_transaccion, rx):
    rx.lpush("Data"+id_transaccion, id_transaccion)