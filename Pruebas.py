from datetime import datetime, timedelta
from datetime import date
import os
import json
import redis
from dotenv import load_dotenv
from SendEmail import EnvioCorreo
import re
import logging

expresion = "<option value='688-000029-96|DEPOSITO|7|ACTIVOS|5600078|Ahorros|BANCOLOMBIA' BANCOLOMBIA - Ahorros - 688-000029-96 </option>"

pattern = r'">[^>]*</option>'  # Expresión regular para buscar texto entre símbolos menor que y mayor que
for match in re.finditer(pattern, expresion):
    print(match.group())



















class MyFilter(logging.Filter):
    def filter(self, record):
        return record.getMessage() != 'basicConfig'

logging.root.addFilter(MyFilter())

logging.debug("This log record will not be output because it is below the level specified in basicConfig")
logging.error("This log record will be output because it passes the filter added to the root logger")





def filter_password(record):
    if 'Connection pool is full, discarding connection' in record.getMessage():
        return False
        print(record.getMessage())
    return True
    print(record.getMessage())

logger = logging.getLogger(__name__)
logger.addFilter(filter_password)

logger.warning('Esta es una')
logger.warning('Esta es una advertencia con Connection pool is full, discarding connection')







load_dotenv()

from mysql.connector import Error
from mysql.connector import pooling







try:
    connection = pooling.MySQLConnectionPool(pool_name="full_pool",
                                                  pool_size=15,
                                                  pool_reset_session=True,
                                                  host='localhost',
                                                  database='practi_bancolombia',
                                                  user='root',
                                                  password='')

    print("Printing connection pool properties ")
    print("Connection Pool Name - ", connection.pool_name)
    print("Connection Pool Size - ", connection.pool_size)

    # Get connection object from a pool
    connection_object = connection.get_connection()

    if connection_object.is_connected():
        db_Info = connection_object.get_server_info()
        print("Connected to MySQL database using connection pool ... MySQL Server version on ", db_Info)

        cursor = connection_object.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("Your connected to - ", record)

except Error as e:
    print("Error while connecting to MySQL using Connection pool ", e)
finally:
    # closing database connection.
    if connection_object.is_connected():
        cursor.close()
        connection_object.close()
        print("MySQL connection is closed")












while True:

    env_list = json.loads(os.environ['ENV_LIST_EXAMPLE'])


    for cite in range(len(env_list)):
        print(env_list[cite])
        #print(env_list[cite])

    """for cite in os.getenv('CUENTAS').split(';'):
        print(cite)"""



    """cuentas = os.getenv('CUENTAS')
    print(len(cuentas))
    for i in range(len(cuentas)):
        print(cuentas[i])"""






















#nueva=   [900.00,200.00,200.00,400.00,400.00]
#antiguas_SQL=[900.00,200.00,200.00,400.00,400.00]

nueva=       ['100.00', '100.00', '100.00', '100.00', '100.00', '100.00', '100.00', '100.00', '0.16', '300.00', '100.00', '200.00', '200.00', '250.00', '100.00', '110.00', '100.00', '100.00', '0.01', '0.03']
antiguas_SQL=['100.00', '100.00', '100.00', '100.00', '100.00', '100.00', '100.00', '100.00', '0.16', '300.00', '100.00', '200.00', '200.00', '250.00', '100.00', '110.00', '100.00', '100.00', '0.01', '0.03']

print(type(nueva))
print(type(antiguas_SQL))

for i in range(15):
    NoSonIguales = 0
    Salir = 0
    for j in range(15):
        print(i," ",j)
        try:
            nueva[i + j]
        except IndexError:
            Salir = 1
            break
        if Salir == 1:
            break
        if nueva[i + j] != antiguas_SQL[j]:
            NoSonIguales = 1
            print("insertando: " + str(nueva[i]))
            print("Ingreso")
            break

        if Salir == 1:
            break
    if Salir == 1:
        break
    if NoSonIguales == 0:
        break

print("For de 10  a 1")
for u in range(10,-1, -1):
    print(u)

if 'Hola' in 'Hola Mundo':  # esto nos devolverá False
    print('doce existe en Docena.')
else:
    print('doce no existe en Docena.')









