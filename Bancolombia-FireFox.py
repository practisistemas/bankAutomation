# Librerias
import logging
import time
import threading
import os
import mysql
import numpy as np
import pandas as pd
import decimal
import selenium
import redis
import re

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, MoveTargetOutOfBoundsException, WebDriverException, \
    InvalidSessionIdException, NoSuchWindowException, TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from Conexion import connection
from Hilos import MantenerSesion,StatusRun
from dotenv import load_dotenv
from Estados import Estados_trabajos
from Trabajos import  cola_de_trabajo
from SendEmail import EnvioCorreo
from datetime import datetime, timedelta
from datetime import date

# load_dotenv = Optiene los resultados de las variables de entorno
load_dotenv()

#Tabla
df = pd.DataFrame()

def main():
    #Configuracion navegador
    options = Options()
    options.headless = False
    driver = webdriver.Firefox(options=options)
    driver.maximize_window()
    # Ingresamos URL
    driver.get('https://sucursalempresas.transaccionesbancolombia.com/SVE/control/BoleTransactional.bancolombia')
    driver.set_window_size(1000, 800)

    try:
        # Digita NIT
        WebDriverWait(driver, 10) \
            .until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input#COMPANYID'))) \
            .send_keys(os.getenv('COMPANYID'))

        # Digita IDENTIFICACION
        WebDriverWait(driver, 10) \
            .until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input#CLIENTID'))) \
            .send_keys(os.getenv('CLIENTID'))

        # CONTRASEÑA
        # posiciona el cursor en el campo
        WebDriverWait(driver, 10) \
            .until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input#USERPASS'))) \
            .send_keys()

        # Contraseña que se va escribir
        password = os.getenv('USERPASS')
        for key in password:
            driver.execute_script("writeAlpha('" + key + "')")
            # driver.execute_script("switchUppercase()")  #convierte en mayus

        # Clic en el boton de ACEPTAR
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.NAME, 'Submit'))).click()

    except TimeoutException as toe:
        # Concatena hora y fecha para  Tomar captura de pantalla
        hoy = date.today()
        hora_actual = datetime.now()
        folio_number = str(hoy) + "-" + str(hora_actual.hour) + "-" + str(hora_actual.minute) + "-" + str(
            hora_actual.second)+str(".png")
        ruta = str(os.getcwd()) + "/Screenshot/"
        driver.get_screenshot_as_file(os.getcwd() + "/Screenshot/" + str(folio_number))

        Mensaje = "Tiempo de respuesta agotado en la ventana de login del servico - Bancolombia Empresas "
        logging.error(Mensaje + str(toe))
        driver.close()
        EnvioCorreo(Mensaje, ruta,folio_number)
        logging.warning("Se reinicio el servico...")
        main()

    except NoSuchWindowException as nswe:
        # Concatena hora y fecha para  Tomar captura de pantalla
        hoy = date.today()
        hora_actual = datetime.now()
        folio_number = str(hoy) + "-" + str(hora_actual.hour) + "-" + str(hora_actual.minute) + "-" + str(
            hora_actual.second)+str(".png")
        ruta = str(os.getcwd()) + "/Screenshot/"
        driver.get_screenshot_as_file(os.getcwd() + "/Screenshot/" + str(folio_number))

        Mensaje = "Se cerro el navegador inesperadamente, se encontraba en la ventana de login "
        logging.error(Mensaje + str(nswe))
        driver.close()
        EnvioCorreo(Mensaje, ruta,folio_number)
        logging.warning("Se reinicio el servico...")
        main()

    except UnexpectedAlertPresentException as uape:
        # Concatena hora y fecha para  Tomar captura de pantalla
        hoy = date.today()
        hora_actual = datetime.now()
        folio_number = str(hoy) + "-" + str(hora_actual.hour) + "-" + str(hora_actual.minute) + "-" + str(
            hora_actual.second)+str(".png")
        ruta = str(os.getcwd()) + "/Screenshot/"
        driver.get_screenshot_as_file(os.getcwd() + "/Screenshot/" + str(folio_number))

        Mensaje = "La información ingresada es incorrecta falta completar algun campo - " +str(uape)
        logging.error(Mensaje)
        EnvioCorreo(Mensaje, ruta,folio_number)

    # Valida si aparece ventana emergente notificando por problema de inicio de sesion o usuario bloqueado
    try:
        driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[1]').is_displayed()
    except NoSuchElementException:
        pass_incorrecta = False
    else:
        pass_incorrecta = True

    if pass_incorrecta == True:
        # Concatena hora y fecha para  Tomar captura de pantalla
        hoy = date.today()
        hora_actual = datetime.now()
        folio_number = str(hoy) + "-" + str(hora_actual.hour) + "-" + str(hora_actual.minute) + "-" + str(
            hora_actual.second)+str(".png")
        ruta = str(os.getcwd()) + "/Screenshot/"
        driver.get_screenshot_as_file(os.getcwd() + "/Screenshot/" + str(folio_number))

        Mensaje= "No se pudo iniciar sesion, datos de ingreso incorrectos, problemas con el servicio de bancolombia o usuario bloqueado, <strong> EL SERVICIO SE REINICIARA EN 15 MINUTOS </strong>"
        logging.error(Mensaje)
        EnvioCorreo(Mensaje, ruta,folio_number)
        driver.close()
        time.sleep(900)
        main()
    else:
        logging.info("INICIO DE SESION EXITOSO")
    #Inicia proceso para acceder al listado de cuentas y transacciones
    try:
        time.sleep(10)
        try:
            driver.switch_to.frame(0)
            WebDriverWait(driver, 80).until(EC.element_to_be_clickable((By.ID, "el1"))).click()
            # Pasos para llegar a la tabla donde se encuentran las cuentas
            #driver.switch_to.frame(0)
            element = driver.find_element(By.ID, 'el1')
            actions = ActionChains(driver)
            actions.move_to_element(element).perform()
            driver.switch_to.default_content()
            driver.switch_to.frame(1)
            element = driver.find_element(By.ID, 'pTR21').click()
            logging.info("INGRESO AL LISTADO DE CUENTAS...")

        except NoSuchElementException:
            # Concatena hora y fecha para  Tomar captura de pantalla
            hoy = date.today()
            hora_actual = datetime.now()
            folio_number = str(hoy) + "-" + str(hora_actual.hour) + "-" + str(hora_actual.minute) + "-" + str(
                hora_actual.second) + str(".png")
            ruta = str(os.getcwd()) + "/Screenshot/"
            driver.get_screenshot_as_file(os.getcwd() + "/Screenshot/" + str(folio_number))

            logging.error("No se pudo desplegar el menu despues del inicio de sesion, SE REINICIA EL SERVICIO")
            driver.get(os.getenv('CERRAR_SESION'))
            time.sleep(2)
            EnvioCorreo("No se pudo desplegar el menu despues del inicio de sesion, SE REINICIA EL SERVICIO", ruta,folio_number)
            driver.close()
            main()

        # conexion REDIS
        try:
            rx = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=os.getenv('REDIS_DB'))
            # Hilo que hace movimientos en la pantalla para evitar cerrra sesion
            # Variable para romper el hilo
            # 1. se elimina la variable para evitar problemas de comunicacion
            rx.delete('Stop_hilo')
            # 2. se crea la variable
            rx.set('Stop_hilo', 0)
        except:
            # Concatena hora y fecha para  Tomar captura de pantalla
            hoy = date.today()
            hora_actual = datetime.now()
            folio_number = str(hoy) + "-" + str(hora_actual.hour) + "-" + str(hora_actual.minute) + "-" + str(
                hora_actual.second) + str(".png")
            ruta = str(os.getcwd()) + "/Screenshot/"
            driver.get_screenshot_as_file(os.getcwd() + "/Screenshot/" + str(folio_number))
            logging.error("No se puede establecer una conexión ya que el equipo de destino denegó expresamente dicha conexión.")
            EnvioCorreo("Redis: No se puede establecer una conexión ya que el equipo de destino denegó expresamente dicha conexión.", ruta,folio_number)

        # Se crea Hilo y se inicializa
        Mantener_sesion = threading.Thread(name="Mantener-Sesion", target=MantenerSesion, args=(
        Select, driver, By, logging, NoSuchWindowException, InvalidSessionIdException, WebDriverException, EnvioCorreo,
        NoSuchElementException, main))
        Mantener_sesion.start()
        logging.info("SE INICIA HILO QUE MANTIENE LA SESION ABIERTA")

        # Inicia iteraciones con WHILE
        while True:
            TransaccionNueva = rx.get('TransaccionNueva')
            if TransaccionNueva == None:
                TransaccionNueva=0
            elif TransaccionNueva == b'0':
                TransaccionNueva=0
            elif TransaccionNueva == b'1':
                TransaccionNueva = 1

            #Cuenta la cantidad de trabajos con ESTADO = 1
            if(TransaccionNueva==0):
                 #Variable para validar si la lista desplegable donde se encuentran las cuentas existe o se encuentra en otra ventana
                ExisteLista=0
                try:
                    driver.find_element(By.NAME, 'accountList')
                except:
                    ExisteLista = 1
                #Valida si se encuentra la listra desblegable donde se seleccionan las cuentas
                if ExisteLista==0:
                    rx.set('Stop_hilo', 0)

                else:
                    # Concatena hora y fecha para  Tomar captura de pantalla
                    hoy = date.today()
                    hora_actual = datetime.now()
                    folio_number = str(hoy) + "-" + str(hora_actual.hour) + "-" + str(hora_actual.minute) + "-" + str(
                        hora_actual.second) + str(".png")
                    ruta = str(os.getcwd()) + "/Screenshot/"
                    driver.get_screenshot_as_file(os.getcwd() + "/Screenshot/" + str(folio_number))

                    logging.error("Hilo que mantiene la sesion abierta no encontro lista de cuentas, SE REINICIA EL SERVICIO")
                    rx.set('Stop_hilo', 2)
                    #Funcion que valida si esta corriendo oo no el aplicativo
                    StatusRun(driver, By, logging, EnvioCorreo, NoSuchElementException, WebDriverException, 2)
                    driver.get(os.getenv('CERRAR_SESION'))
                    time.sleep(10)
                    EnvioCorreo("Error: Hilo que mantiene la sesion abierta no encontro lista de cuentas, SE REINICIA EL SERVICIO", ruta,folio_number)
                    driver.close()
                    main()
            else:
                logging.info("Se encontraron transacciones nuevas")
                rx.set('Stop_hilo', 1)
                rx.set('TransaccionNueva',0)

                try:
                    global MyCursor0
                    MyCursor0 = connection.cursor()
                    #MyCursor0.autocommit = True
                    MyCursor0.execute("SELECT * FROM trabajo WHERE estado = 1 ")
                    MyResult = MyCursor0.fetchall()

                except mysql.connector.Error as error:
                    print(f"Error: {error}")
                finally:
                    MyCursor0.close()

                # Ingresar cuenta por cuenta
                for x in MyResult:
                    id_trabajo = str(x[0])
                    nombre_cuenta = str(x[1])

                    ExisteCuenta=1
                    try:
                        # Despliega la lista donde se encuentran las cuentas
                        select = Select(driver.find_element(By.NAME, 'accountList'))
                        Nom_cuenta= "BANCOLOMBIA - Ahorros - "+ str(x[1])
                        select.select_by_visible_text(str(Nom_cuenta))
                    except NoSuchElementException:
                        ExisteCuenta = 0


                    if ExisteCuenta ==1:
                        # Validacion si la cuenta tiene o no data y si tiene procede a extraerla
                        #Busca "NO EXISTEN REGISTROS QUE CUMPLAN CON EL CRITERIO DE BUSQUEDA SELECCIONADO" para validar si tiene o no tabla con registros
                        try:
                            driver.find_element(By.XPATH, '/html/body/table/tbody/tr[1]/td/div/table[4]/tbody/tr/td[2]').is_displayed()
                        except NoSuchElementException:
                            link = True
                        else:
                            link = False

                        if(link == True):
                            logging.info("Existen transacciones en la cuenta: " + str(x[1]))
                            # Extrae informacion de las tablas y numero de columnas y filas
                            cols = driver.find_elements(By.XPATH, '/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr[4]/td')
                            rows = driver.find_elements(By.XPATH, '/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr')
                            rows1 = len(rows) - 1
                            #Crea tabla para almacenar los registros
                            df = pd.DataFrame(columns=['hora','fecha', 'fecha_aplicacion', 'correccion','descripcion','documento','referencia','oficina','saldo_canje','valor'])
                            for ro in range(1, rows1):
                                try:
                                    hora = driver.find_element(By.XPATH,"/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr[4]/td/table/tbody/tr[" + str(ro) + "]/td[1]").text
                                    fecha = driver.find_element(By.XPATH,"/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr[4]/td/table/tbody/tr[" + str(ro) + "]/td[2]").text
                                    fecha_aplicacion = driver.find_element(By.XPATH,"/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr[4]/td/table/tbody/tr[" + str(ro) + "]/td[3]").text
                                    correccion = driver.find_element(By.XPATH,"/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr[4]/td/table/tbody/tr[" + str(ro) + "]/td[4]").text
                                    descripcion = driver.find_element(By.XPATH,"/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr[4]/td/table/tbody/tr[" + str(ro) + "]/td[5]").text
                                    documento = driver.find_element(By.XPATH,"/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr[4]/td/table/tbody/tr[" + str(ro) + "]/td[6]").text
                                    referencia = driver.find_element(By.XPATH,"/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr[4]/td/table/tbody/tr[" + str(ro) + "]/td[7]").text
                                    oficina = driver.find_element(By.XPATH,"/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr[4]/td/table/tbody/tr[" + str(ro) + "]/td[8]").text
                                    saldo_canje = driver.find_element(By.XPATH,"/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr[4]/td/table/tbody/tr[" + str(ro) + "]/td[9]").text
                                    valor = driver.find_element(By.XPATH,"/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr[4]/td/table/tbody/tr[" + str(ro) + "]/td[10]").text
                                except:
                                    break

                                # Valida si el documento viene vacio
                                documentoFinal = documento.strip()
                                if (documentoFinal == ''):
                                    documento = 0
                                # quita las , del valor  y los espacios en blanco al inicio y al final de valor
                                valorPreliminar = valor.replace(",", "")
                                valorFinal = valorPreliminar.strip()
                                referencia = referencia.strip()
                                oficina = oficina.strip()
                                saldoCanjePreliminar = saldo_canje.replace(",", "")
                                saldoCanjeFinal = saldoCanjePreliminar.strip()

                                #Romper ciclo
                                if(hora == "  "):
                                    print("Ingreso al break")
                                    break

                                if 'TRANSF QR' in descripcion:
                                    # LLenar DataFrame
                                    d = {'hora': hora,
                                         'fecha': fecha,
                                         'fecha_aplicacion': fecha_aplicacion,
                                         'correccion': correccion,
                                         'descripcion': descripcion,
                                         'documento': documento,
                                         'referencia': referencia,
                                         'oficina': oficina,
                                         'saldo_canje': saldoCanjeFinal,
                                         'valor': valorFinal}
                                    df = pd.concat([df, pd.DataFrame(d, index=[0])], ignore_index=True)
                            logging.info(df)

                            # Crea tabla para almacenar los registros
                            ### optiene las ultimas 20 transaciones de la cuenta
                            today = date.today()
                            global  result_SQL
                            try:
                                MyCursor2 = connection.cursor()
                                sql6 = "SELECT Hora FROM tiempo_real WHERE Fecha= %s AND Cuenta = %s  ORDER BY Id DESC LIMIT 1"
                                val6 = (today, str(x[1]))
                                MyCursor2.execute(sql6, val6)
                                result_SQL = MyCursor2.fetchone()
                            except mysql.connector.Error as error:
                                print(f"Error: {error}")
                            finally:
                                MyCursor2.close()

                            pos = []
                            guardar = 0
                            cont = 0
                            if result_SQL == None:
                                for k in range(len(df["valor"])):
                                    pos.append(k)
                                    guardar += 1
                            else:
                                for k in df["hora"]:
                                    result = re.sub('[^0-9:]', '', k)
                                    hora1 = datetime.strptime(result, '%H:%M:%S').time()
                                    hora2 = datetime.strptime(str(result_SQL[0]), '%H:%M:%S').time()

                                    if  hora1 > hora2:
                                        guardar += 1
                                        pos.append(k)
                            logging.info(pos)
                            # Inserta los registros en la base de datos
                            if guardar >= 1:
                                try:
                                    val1 = []
                                    MyCursor3 = connection.cursor()
                                    sql1 = """INSERT INTO tiempo_real(Hora, Fecha, Fecha_aplicacion, Correccion, Descripcion, Documento, Referencia, Oficina, Saldo_canje, Valor, Cuenta, Id_trabajo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                                    tamano = len(pos) - 1
                                    #Se da vuelta al array para obtener los valores de atras hacia adelante
                                    for i in range(tamano, -1, -1):
                                        val1.append((
                                            df.loc[i, "hora"], df.loc[i, "fecha"], df.loc[i, "fecha_aplicacion"], df.loc[i, "correccion"], df.loc[i, "descripcion"], df.loc[i, "documento"], df.loc[i, "referencia"],
                                            df.loc[i, "oficina"], df.loc[i, "saldo_canje"], df.loc[i, "valor"], str(x[1]), str(x[0])))
                                    MyCursor3.executemany(sql1, val1)
                                    connection.commit()
                                    cont += 1

                                except mysql.connector.errors.ProgrammingError as error:
                                    connection.rollback()
                                    logging.error("No se insertaron registros de la cuenta " + str(x[1]))
                                except mysql.connector.errors as eu:
                                    connection.rollback()
                                    logging.error("rollback"+eu)
                                except AttributeError as ae:
                                    logging.error("AttributeError"+ae)
                                finally:
                                    MyCursor3.close()
                                    #break
                            else:
                                logging.info("No se encontraron transacciones nuevas")

                            # Validacion para registrar que no han habido pagos nuevos con estado 3
                            if(cont ==0):
                                #Se actualiza el estado a 3 NO EXISTEN NUEVOS PAGOS
                                logging.warning("No se registraron pagos nuevos en la cuenta " + str(x[1]))
                                id_estado = 4
                                Estados_trabajos(connection, logging, mysql, id_trabajo, nombre_cuenta, id_estado)
                                id_transaccion= str(x[0])
                                cola_de_trabajo(id_transaccion)
                            else:
                                #Se actualiza el estado a 1 EXISTEN NUEVOS PAGOS
                                logging.warning("Se registraron pagos a la cuenta" + str(x[1]))
                                id_estado = 2
                                Estados_trabajos(connection, logging, mysql, id_trabajo, nombre_cuenta, id_estado)
                                id_transaccion = str(x[0])
                                cola_de_trabajo(id_transaccion)

                        else:
                            # Actualiza el estado del trabajo a ESTADO = 2 para no ser procesado de nuevo
                            logging.warning("No existen registros que cumplan con el criterio de búsqueda seleccionado - " + str(x[1]))
                            id_estado = 3
                            Estados_trabajos(connection,logging,mysql,id_trabajo,nombre_cuenta,id_estado)
                            id_transaccion = str(x[0])
                            cola_de_trabajo(id_transaccion)

                        # Se termina de realizar la extraccion de la informacion y se reaunda el Hilo
                        StatusHilo = Mantener_sesion.is_alive()
                        print("Status hilo: "+ str(StatusHilo))
                        rx.set('Stop_hilo', 0)

                    else:
                        # Concatena hora y fecha para  Tomar captura de pantalla
                        hoy = date.today()
                        hora_actual = datetime.now()
                        folio_number = str(hoy) + "-" + str(hora_actual.hour) + "-" + str(
                            hora_actual.minute) + "-" + str(
                            hora_actual.second) + str(".png")
                        ruta = str(os.getcwd()) + "/Screenshot/"
                        driver.get_screenshot_as_file(os.getcwd() + "/Screenshot/" + str(folio_number))

                        logging.warning("El numero de cuenta no existe - " + str(x[1]))
                        id_estado = 6
                        Estados_trabajos(connection, logging, mysql, id_trabajo, nombre_cuenta, id_estado)
                        id_transaccion = str(x[0])
                        cola_de_trabajo(id_transaccion)
                        EnvioCorreo("El numero de cuenta no existe - " + str(x[1]), ruta,folio_number)
                        rx.set('Stop_hilo', 0)

    except NoSuchElementException as NSEE:
        # Concatena hora y fecha para  Tomar captura de pantalla
        hoy = date.today()
        hora_actual = datetime.now()
        folio_number = str(hoy) + "-" + str(hora_actual.hour) + "-" + str(hora_actual.minute) + "-" + str(
            hora_actual.second)+str(".png")
        ruta = str(os.getcwd()) + "/Screenshot/"
        driver.get_screenshot_as_file(os.getcwd() + "/Screenshot/" + str(folio_number))

        logging.error("Problemas al cargar el sitio principal, se reinicia el servicio: "+str(NSEE))
        driver.get(os.getenv('CERRAR_SESION'))
        time.sleep(2)
        EnvioCorreo("Problemas al cargar el sitio, SE REINICIA EL SERVICIO", ruta,folio_number)
        driver.close()
        main()

    except MoveTargetOutOfBoundsException:
        logging.error("Problemas al desplegar el menu")
        time.sleep(3)
        driver.switch_to.frame(0)
        driver.find_element(By.ID, 'el15').click()
        driver.close()

    except WebDriverException as WD:
        #logging.error("Se cerro inesperadamente el navegador "+ str(WD))
        #driver.close()
        print(WD)

    except InvalidSessionIdException as IE:
        logging.error("Se detuvo el hilo de sesion inesperadamente  " + str(IE))
        rx.set('Stop_hilo', 1)

if __name__ =="__main__":
    main()






