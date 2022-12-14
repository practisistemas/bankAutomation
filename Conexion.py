import mysql.connector
import os
import logging
from mysql.connector import Error
from dotenv import load_dotenv
from SendEmail import EnvioCorreo

load_dotenv()

logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        filename='bancolombia.log',
                        filemode='a')
try:
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        user=os.getenv('DB_USER'),
        password=os.getenv('BD_PASSWORD'),
        db=os.getenv('DB'),
        pool_size=5,
    )

    if connection.is_connected():
        infoServer = connection.get_server_info()
        cursor = connection.cursor()
        #cursor.execute("SELECT DATABASE()")
        #row = cursor.fetchone()
        #print("Conectado a la base de datos: {}".format(row))
        logging.info("CONEXION EXITOSA.")
except Error as ex:
    Mensaje = "Error durante la conexión a base de datos: {}".format(ex)
    EnvioCorreo(Mensaje)
    logging.error("Error durante la conexión a base de datos: {}".format(ex))

finally:
    if connection.is_connected():
        logging.info("SE ABRE CURSOR DE BASE DE DATOS")
        #connection.close()  # Se cerró la conexión a la BD.
        #print("La conexión ha finalizado.")