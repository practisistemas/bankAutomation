import time
import os
import redis

# conexion REDIS
r = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'),db=os.getenv('REDIS_DB'), charset='utf-8', decode_responses =True)

def MantenerSesion(Select, driver, By,logging, NoSuchWindowException, InvalidSessionIdException, WebDriverException, EnvioCorreo, NoSuchElementException):
    try:
        while True:
            Stop_hilo = r.get('Stop_hilo')
            if(str(Stop_hilo) == '0'):
                print("Ejecutando el Hilo")
                try:
                    select = Select(driver.find_element(By.NAME, 'accountForDetail'))
                    Nom_cuenta1 = "BANCOLOMBIA - Ahorros - "+os.getenv('HILO_CUENTA_1')
                    select.select_by_visible_text(str(Nom_cuenta1))
                except NoSuchElementException:
                    logging.warning("Error no se encontro lista de cuentas, se reinicia el servicio")
                # Espera 40 segundos
                time.sleep(40)

                if (str(Stop_hilo) == '0'):

                    try:
                        select1 = Select(driver.find_element(By.NAME, 'accountForDetail'))
                        Nom_cuenta2 = "BANCOLOMBIA - Ahorros - "+os.getenv('HILO_CUENTA_2')
                        select1.select_by_visible_text(str(Nom_cuenta2))
                    except NoSuchElementException:
                        logging.warning("Error no se encontro lista de cuentas, se reinicia el servicio")
                    # Espera 40 segundos
                    time.sleep(40)
                else:
                    logging.warning("Se detiene hilo que mantiene la sesión abierta")
                    break
            else:
                logging.warning("Se detiene hilo que mantiene la sesión abierta")
                break
    except NoSuchWindowException as ns:
        logging.error("Se detiene hilo que mantiene la sesión abierta por cierre inesperado del navegador: "+str(ns))

    except WebDriverException as we:
        logging.error("Se detiene hilo que mantiene la sesión abierta por cierre inesperado del navegador: " + str(we))





def CerrarSesion(driver,By, logging):
    while True:
        Cerrar_Sesion = r.get('Close_site')

        if(str(Cerrar_Sesion) == '1'):
            time.sleep(3)
            logging.error("Se procede a cerrar sesion y reiniciar la ejecucion")
            time.sleep(3)
            driver.switch_to.frame(0)
            driver.find_element(By.ID, 'el15').click()
            driver.close()









