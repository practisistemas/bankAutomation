import redis
from Conexion import connection
import mysql
import redis
import os

from dotenv import load_dotenv

#r = redis.Redis(host='localhost', port=6379,db=0)
#r.blpop('Hola mundo', 50)
#r.rpush('transacti', 'Holaaaaa')
load_dotenv()

try:
    r = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'),db=os.getenv('REDIS_DB'))

except:
    print("Hola")
print("Hola")
r.set('Stop_hilo', 1)
#r.lpush("Data" + str(17), 900)










"""try:
    MyCursor = connection.cursor()
    sql2 = "INSERT INTO trabajo( Cuenta, Estado) VALUES ('3434-00', 0) "
    MyCursor.execute(sql2)
    connection.commit()

    id = MyCursor.lastrowid
    com = str(id)
    print(MyCursor.lastrowid)
    r.blpop(com, 120)
except mysql.connector.errors.ProgrammingError as error:
    connection.rollback()
except mysql.connector.errors as ey:
    connection.rollback()
finally:
    MyCursor.close()"""