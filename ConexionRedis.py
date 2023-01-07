import os
import redis
from dotenv import load_dotenv

load_dotenv()

class ConexRedis:
    def ConRedis(logging, EnvioCorreo,driver):
        try:
          return  redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=os.getenv('REDIS_DB'), charset='utf-8', decode_responses =True)
        except:
            logging.error("No se puede establecer una conexión ya que el equipo de destino denegó expresamente dicha conexión.")
            Mensaje = "Redis: No se puede establecer una conexión ya que el equipo de destino denegó expresamente dicha conexión."
            EnvioCorreo(Mensaje, driver)