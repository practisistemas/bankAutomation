import time
import os
import redis
import json
import threading
from datetime import datetime, timedelta
from datetime import date
from dotenv import load_dotenv

load_dotenv()
def MantenerSesion(Select, driver, By,logging, NoSuchWindowException, WebDriverException, EnvioCorreo, NoSuchElementException, rx):
    try:
        while True:
            Stop_hilo = rx.get('Stop_hilo')
            if(str(Stop_hilo) == '0'):
                print("Ejecutando el Hilo")
                # Obtiene el título de la página
                title = driver.title
                if title == "":
                    print("El navegador se cerro")
                try:
                    #Extrae las cuentas del archivo .env
                    cuentas_list = json.loads(os.environ['CUENTAS'])
                    for k in range(len(cuentas_list)):
                        #Valida si el elemento esta disabled o no
                        element = driver.find_element(By.NAME, 'accountList')
                        if element.get_attribute("disabled"):
                            print("Element is disabled")
                            logging.warning("Se encontro lista de cuentas en ESTADO DISABLED")
                            driver.execute_script("arguments[0].disabled = false", element)
                            Mensaje = "Error: Se encontro lista de cuentas en <strong>ESTADO DISABLED</strong> -  SE CAMBIA EL ESTADO A ENABLE"
                            EnvioCorreo(Mensaje, driver)
                        #Itera entre todas las cuntas
                        select = Select(driver.find_element(By.NAME, 'accountList'))
                        Nom_cuenta1 = "BANCOLOMBIA - Ahorros - "+str(cuentas_list[k])
                        select.select_by_visible_text(str(Nom_cuenta1))
                        #Mantiene un tiempo de espera de 40 segundos,
                        for h in range(21):
                            StatusRun(driver, By, logging, EnvioCorreo, NoSuchElementException, WebDriverException, 1, rx)
                            time.sleep(1)

                except NoSuchElementException:
                    logging.warning("No se encontro lista de cuentas")
                    element = driver.find_element(By.NAME, 'accountList')
                    if element.get_attribute("disabled"):
                        print("Element is disabled")
                        logging.warning("No se encontro lista de cuentas - ESTADO DISABLED")

            elif(str(Stop_hilo) == '2'):
                logging.warning("Se detiene hilo que mantiene la sesión abierta")
                break
            elif (str(Stop_hilo) == '1'):
                logging.warning("Esperando a terminar de procesar transacciones")

    except NoSuchWindowException as ns:
        logging.error("Se detiene hilo que mantiene la sesión abierta por cierre inesperado del navegador: "+str(ns))
        Mensaje = "Se detiene hilo que mantiene la sesión abierta por cierre inesperado del navegador"
        EnvioCorreo(Mensaje, driver)

    except WebDriverException as we:
        logging.error("Se detiene hilo que mantiene la sesión abierta por cierre inesperado del navegador: "+str(we))
        Mensaje = "Se detiene hilo que mantiene la sesión abierta por cierre inesperado del navegador"
        EnvioCorreo(Mensaje, driver)

def StatusRun(driver, By,logging, EnvioCorreo, NoSuchElementException,WebDriverException, rango, rx):
    for o in range(rango):
        element = driver.find_elements(By.NAME, "accountList")
        if element:
            # Element exists
            rx.set('StatusService', 1)
            rx.expire('StatusService', 60)
        else:
            # Element does not exist
            print("Element not found")
            rx.set('StatusService', 0)
            rx.expire('StatusService', 30)

        time.sleep(1)
        Stop_hilo = rx.get('Stop_hilo')
        if (str(Stop_hilo) == '0'):
            break






