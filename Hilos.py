import time
import os
import redis
import threading

# conexion REDIS
r = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'),db=os.getenv('REDIS_DB'), charset='utf-8', decode_responses =True)

def MantenerSesion(Select, driver, By,logging, NoSuchWindowException, InvalidSessionIdException, WebDriverException, EnvioCorreo, NoSuchElementException,main):
    try:
        while True:
            Stop_hilo = r.get('Stop_hilo')
            if(str(Stop_hilo) == '0'):
                print("Ejecutando el Hilo")
                try:
                    select = Select(driver.find_element(By.NAME, 'accountList'))
                    Nom_cuenta1 = "BANCOLOMBIA - Ahorros - "+os.getenv('HILO_CUENTA_1')
                    select.select_by_visible_text(str(Nom_cuenta1))

                except NoSuchElementException:
                    element = driver.find_element(By.NAME, 'accountList')
                    if element.get_attribute("disabled"):
                        print("Element is disabled")
                        logging.warning("No se encontro lista de cuentas - ESTADO DISABLED")
                    else:
                        logging.warning("No se encontro lista de cuentas")
            elif(str(Stop_hilo) == '2'):
                logging.warning("Se detiene hilo que mantiene la sesión abierta")
                break
            elif (str(Stop_hilo) == '1'):
                logging.warning("Esperando a terminar de procesar transacciones")

            for h in range(21):
                StatusRun(driver, By, logging, EnvioCorreo, NoSuchElementException, WebDriverException, 1)
                time.sleep(1)

            if (str(Stop_hilo) == '0'):
                try:
                    select1 = Select(driver.find_element(By.NAME, 'accountList'))
                    Nom_cuenta2 = "BANCOLOMBIA - Ahorros - "+os.getenv('HILO_CUENTA_2')
                    select1.select_by_visible_text(str(Nom_cuenta2))
                except NoSuchElementException:
                    element = driver.find_element(By.NAME, 'accountList')
                    if element.get_attribute("disabled"):
                        print("Element is disabled")
                        logging.warning("No se encontro lista de cuentas - ESTADO DISABLED")
                    else:
                        logging.warning("No se encontro lista de cuentas")

            elif (str(Stop_hilo) == '2'):
                logging.warning("Se detiene hilo que mantiene la sesión abierta")
                break
            elif (str(Stop_hilo) == '1'):
                logging.warning("Esperando a terminar de procesar transacciones")

            for h in range(21):
                StatusRun(driver, By, logging, EnvioCorreo, NoSuchElementException, WebDriverException, 1)
                time.sleep(1)

    except NoSuchWindowException as ns:
        logging.error("Se detiene hilo que mantiene la sesión abierta por cierre inesperado del navegador: "+str(ns))
        #StatusRun(driver, By, logging, EnvioCorreo, NoSuchElementException, 1)

    except WebDriverException as we:
        logging.error("Se detiene hilo que mantiene la sesión abierta por cierre inesperado del navegador: " + str(we))
        #StatusRun(driver, By, logging, EnvioCorreo, NoSuchElementException, 1)


def StatusRun(driver, By,logging, EnvioCorreo, NoSuchElementException,WebDriverException, rango):
    for o in range(rango):
        element = driver.find_elements(By.NAME, "accountList")
        if element:
            # Element exists
            r.set('StatusService', 1)
            r.expire('StatusService', 60)
        else:
            # Element does not exist
            print("Element not found")
            r.set('StatusService', 0)
            r.expire('StatusService', 60)
        time.sleep(1)
        Stop_hilo = r.get('Stop_hilo')
        if (str(Stop_hilo) == '0'):
            break






