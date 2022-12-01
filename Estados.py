
def Estados_trabajos(connection,logging,mysql,id_trabajo,nombre_cuenta, id_estado):
    try:
        MyCursor = connection.cursor()
        sql5 = "UPDATE trabajo SET Estado = %s WHERE Id = %s "
        val5 = (id_estado,id_trabajo)
        MyCursor.execute(sql5, val5)
        connection.commit()
    except mysql.connector.errors.ProgrammingError as error:
        connection.rollback()
        logging.error("No se puedo actualizar el estado de la cola de trabajo para la cuenta " + nombre_cuenta + " con ID " + id_trabajo + "   "+error)
    except mysql.connector.errors as ey:
        connection.rollback()
        logging.error(ey)
    finally:
        MyCursor.close()