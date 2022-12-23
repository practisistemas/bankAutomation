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
                    logging.warning("No se encontro lista de cuentas")
                    time.sleep(2)
                StatusRun(driver, By, logging, EnvioCorreo, NoSuchElementException,WebDriverException,20)
            elif(str(Stop_hilo) == '2'):
                logging.warning("Se detiene hilo que mantiene la sesión abierta")
                break
            else:
                logging.warning("Esperando a terminar de procesar transacciones")

            if (str(Stop_hilo) == '0'):
                try:
                    select1 = Select(driver.find_element(By.NAME, 'accountList'))
                    Nom_cuenta2 = "BANCOLOMBIA - Ahorros - "+os.getenv('HILO_CUENTA_2')
                    select1.select_by_visible_text(str(Nom_cuenta2))
                except NoSuchElementException:
                    logging.warning("Error no se encontro lista de cuentas")
                    time.sleep(2)
                StatusRun(driver, By, logging, EnvioCorreo, NoSuchElementException,WebDriverException,20)
            elif (str(Stop_hilo) == '2'):
                logging.warning("Se detiene hilo que mantiene la sesión abierta")
                break
            else:
                logging.warning("Esperando a terminar de procesar transacciones")

    except NoSuchWindowException as ns:
        logging.error("Se detiene hilo que mantiene la sesión abierta por cierre inesperado del navegador: "+str(ns))
        StatusRun(driver, By, logging, EnvioCorreo, NoSuchElementException, 3)

    except WebDriverException as we:
        logging.error("Se detiene hilo que mantiene la sesión abierta por cierre inesperado del navegador: " + str(we))
        StatusRun(driver, By, logging, EnvioCorreo, NoSuchElementException, 3)


def StatusRun(driver, By,logging, EnvioCorreo, NoSuchElementException,WebDriverException, rango):
    for o in range(rango):
        try:
            driver.find_element(By.NAME, 'accountList').is_displayed()
        except NoSuchElementException:
            link = True
            r.set('StatusSerice', 0)
        except WebDriverException:
            link = True
            r.set('StatusSerice', 0)
        else:
            link = False
        if link==True:
            r.set('StatusSerice', 0)
        else:
            r.set('StatusSerice', 1)
        time.sleep(10)
        Stop_hilo = r.get('Stop_hilo')
        if (str(Stop_hilo) == '0'):
            break






