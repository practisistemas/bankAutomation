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
from Hilos import MantenerSesion
from dotenv import load_dotenv
from Estados import Estados_trabajos
from Trabajos import  cola_de_trabajo
from SendEmail import EnvioCorreo


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
        Mensaje = "Tiempo de respuesta agotado en la ventana de login del servico - Bancolombia Empresas "
        logging.error(Mensaje + str(toe))
        driver.close()
        EnvioCorreo(Mensaje)
        logging.warning("Se reinicio el servico...")
        main()

    except NoSuchWindowException as nswe:
        Mensaje = "Se cerro el navegador inesperadamente, se encontraba en la ventana de login "
        logging.error(Mensaje + str(nswe))
        driver.close()
        EnvioCorreo(Mensaje)
        logging.warning("Se reinicio el servico...")
        main()

    except UnexpectedAlertPresentException as uape:
        Mensaje = "La información ingresada es incorrecta falta completar algun campo - " +str(uape)
        logging.error(Mensaje)
        EnvioCorreo(Mensaje)

    # Valida si aparece ventana emergente notificando por problema de inicio de sesion o usuario bloqueado
    try:
        driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div[1]').is_displayed()
    except NoSuchElementException:
        pass_incorrecta = False
    else:
        pass_incorrecta = True

    if pass_incorrecta == True:
        Mensaje= "No se pudo iniciar sesion, datos de ingreso incorrectos, problemas con el servicio de bancolombia o usuario bloqueado, <strong> EL SERVICIO SE REINICIARA EN 15 MINUTOS </strong>"
        logging.error(Mensaje)
        EnvioCorreo(Mensaje)
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
            element = driver.find_element(By.ID, 'pTR18')
            actions = ActionChains(driver)
            actions.move_to_element(element).perform()
            btn = driver.find_element(By.ID, 'lnk11')
            driver.execute_script("arguments[0].click();", btn)
            logging.info("INGRESO AL LISTADO DE CUENTAS...")

        except NoSuchElementException:
            logging.error("No se pudo desplegar el menu despues del inicio de sesion, SE REINICIA EL SERVICIO")
            driver.get(os.getenv('CERRAR_SESION'))
            time.sleep(2)
            EnvioCorreo("No se pudo desplegar el menu despues del inicio de sesion, SE REINICIA EL SERVICIO")
            driver.close()
            main()

        # Ingresa a la primera cuenta para realizar proceso de extraccion de informacion
        WebDriverWait(driver, 50).until(EC.element_to_be_clickable((By.XPATH, "/html/body/table/tbody/tr/td/div/form[2]/table[1]/tbody/tr[1]/td[3]/a"))).click()
        logging.info("INICIA PROCESO DE VALIDACION Y EXTRACCION DE TRANSACCIONES...")
        time.sleep(3)

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
            logging.error("No se puede establecer una conexión ya que el equipo de destino denegó expresamente dicha conexión.")
            EnvioCorreo("Redis: No se puede establecer una conexión ya que el equipo de destino denegó expresamente dicha conexión.")

        # Se crea Hilo y se inicializa
        Mantener_sesion = threading.Thread(name="Mantener-Sesion", target=MantenerSesion, args=(
        Select, driver, By, logging, NoSuchWindowException, InvalidSessionIdException, WebDriverException, EnvioCorreo,
        NoSuchElementException, main))
        Mantener_sesion.start()
        logging.info("SE INICIA HILO QUE MANTIENE LA SESION ABIERTA")
        print("Se salio del WHILE")

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
                    driver.find_element(By.NAME, 'accountForDetail')
                except:
                    ExisteLista = 1

                #Valida si se encuentra la listra desblegable donde se seleccionan las cuentas
                if ExisteLista==0:
                    rx.set('Stop_hilo', 0)
                else:
                    logging.error("Hilo que mantiene la sesion abierta no encontro lista de cuentas, se reinicia el servicio")
                    rx.set('Stop_hilo', 1)
                    driver.get(os.getenv('CERRAR_SESION'))
                    time.sleep(10)
                    EnvioCorreo("Error: Hilo que mantiene la sesion abierta no encontro lista de cuentas, se reinicia el servicio")
                    driver.close()
                    main()

            else:
                logging.info("Se encontraron transacciones nuevas")
                rx.set('Stop_hilo', 1)
                rx.set('TransaccionNueva',0)

                try:
                    #global MyCursor0
                    MyCursor0 = connection.cursor()
                    #MyCursor0.autocommit = True
                    MyCursor0.execute("SELECT * FROM trabajo WHERE estado = 1 ")
                    MyResult = MyCursor0.fetchall()
                finally:
                    MyCursor0.close()

                # Ingresar cuenta por cuenta
                for x in MyResult:
                    id_trabajo = str(x[0])
                    nombre_cuenta = str(x[1])

                    ExisteCuenta=1
                    try:
                        # Despliega la lista donde se encuentran las cuentas
                        select = Select(driver.find_element(By.NAME, 'accountForDetail'))
                        Nom_cuenta= "BANCOLOMBIA - Ahorros - "+ str(x[1])
                        select.select_by_visible_text(str(Nom_cuenta))
                    except NoSuchElementException:
                        ExisteCuenta = 0


                    if ExisteCuenta ==1:
                        # Validacion si la cuenta tiene o no data y si tiene procede a extraerla
                        #Busca "NO EXISTEN REGISTROS QUE CUMPLAN CON EL CRITERIO DE BUSQUEDA SELECCIONADO" para validar si tiene o no tabla con registros
                        try:
                            driver.find_element(By.XPATH, '/html/body/div[43]/table[3]/tbody/tr[4]/td/table/tbody/tr/td[2]').is_displayed()
                        except NoSuchElementException:
                            link = True
                        else:
                            link = False

                        if(link == True):
                            logging.info("Existen transacciones en la cuenta: " + str(x[1]))
                            # Extrae informacion de las tablas y numero de columnas y filas
                            cols = driver.find_elements(By.XPATH, '/html/body/div[43]/p[2]/table[1]/tbody/tr[1]/td')
                            rows = driver.find_elements(By.XPATH, '/html/body/div[43]/p[2]/table[1]/tbody/tr')
                            rows1 = 1 + len(rows)

                            #Crea tabla para almacenar los registros
                            df = pd.DataFrame(columns=['fecha', 'descripcion', 'sucursal','referencia_1','referencia_2','documento','valor'])
                            for ro in range(1, rows1):
                                fecha = driver.find_element(By.XPATH,"/html/body/div[43]/p[2]/table[1]/tbody/tr[" + str(ro) + "]/td[1]").text
                                descripcion = driver.find_element(By.XPATH,"/html/body/div[43]/p[2]/table[1]/tbody/tr[" + str(ro) + "]/td[2]").text
                                sucursal = driver.find_element(By.XPATH,"/html/body/div[43]/p[2]/table[1]/tbody/tr[" + str(ro) + "]/td[3]").text
                                referencia_1 = driver.find_element(By.XPATH,"/html/body/div[43]/p[2]/table[1]/tbody/tr[" + str(ro) + "]/td[4]").text
                                referencia_2 = driver.find_element(By.XPATH,"/html/body/div[43]/p[2]/table[1]/tbody/tr[" + str(ro) + "]/td[5]").text
                                documento = driver.find_element(By.XPATH,"/html/body/div[43]/p[2]/table[1]/tbody/tr[" + str(ro) + "]/td[6]").text
                                valor = driver.find_element(By.XPATH,"/html/body/div[43]/p[2]/table[1]/tbody/tr[" + str(ro) + "]/td[7]").text

                                # Valida si el documento viene vacio
                                documentoFinal = documento.strip()
                                if (documentoFinal == ''):
                                    documento = 0

                                # quita las , del valor  y los espacios en blanco al inicio y al final de valor
                                valorPreliminar = valor.replace(",", "")
                                valorFinal = valorPreliminar.strip()

                                referencia_1_1 = referencia_1.strip()
                                referencia_2_2 = referencia_2.strip()

                                #LLenar DataFrame
                                d = {'fecha':fecha,
                                     'descripcion':descripcion,
                                     'sucursal':sucursal,
                                     'referencia_1':referencia_1_1,
                                     'referencia_2':referencia_2_2,
                                     'documento':documento,
                                     'valor':valorFinal}

                                df = pd.concat([df, pd.DataFrame(d, index=[0])], ignore_index=True)

                            # Crea tabla para almacenar los registros
                            ### optiene las ultimas 20 transaciones de la cuenta
                            try:
                                MyCursor2 = connection.cursor()
                                sql6 = "SELECT Valor FROM tiempo_real WHERE cuenta= %s  order by id ASC  LIMIT 20 "
                                val6 = (str(x[1]),)
                                MyCursor2.execute(sql6, val6)
                                result_SQL = MyCursor2.fetchall()
                                antiguas_SQL = []
                                for row in result_SQL:
                                    antiguas_SQL.append(str(row[0]))
                            finally:
                                MyCursor2.close()
                            global nueva
                            #nueva = df["valor"].to_numpy()
                            nueva = list(df["valor"])

                            guardar = 0
                            pos = []
                            cont = 0
                            if len(antiguas_SQL) ==0:
                                guardar += 1
                                for k in range(len(nueva)):
                                    pos.append(k)
                                print(pos)
                            else:

                                #Valida nuevas transaxxiones
                                for i in range(len(antiguas_SQL)):
                                    NoSonIguales = 0
                                    Salir = 0
                                    for j in range(len(antiguas_SQL)):
                                        print(i, " ", j)
                                        try:
                                            nueva[i + j]
                                        except IndexError:
                                            Salir = 1
                                            break
                                        if Salir == 1:
                                            break
                                        if nueva[i + j] != antiguas_SQL[j]:
                                            NoSonIguales = 1
                                            break

                                        if Salir == 1:
                                            break
                                    if Salir == 1:
                                        break
                                    if NoSonIguales == 0:
                                        break

                            print(pos)
                            # Inserta los registros en la base de datos
                            if guardar >= 1:
                                try:
                                    val1 = []
                                    MyCursor3 = connection.cursor()
                                    sql1 = """INSERT INTO tiempo_real(Fecha, Descripcion, Sucursal_canal, Referencia_1, Referencia_2, Documento, Valor, Cuenta, Id_trabajo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                                    #for i in range(len(df)):
                                    for i in pos:
                                        val1.append((
                                            df.loc[i, "fecha"], df.loc[i, "descripcion"], df.loc[i, "sucursal"], df.loc[i, "referencia_1"], df.loc[i, "referencia_2"], df.loc[i, "documento"],
                                            df.loc[i, "valor"], str(x[1]), str(x[0])))
                                    MyCursor3.executemany(sql1, val1)

                                    connection.commit()
                                    cont += 1

                                except mysql.connector.errors.ProgrammingError as error:
                                    connection.rollback()
                                    logging.error("No se insertaron registros de la cuenta " + str(x[1]))
                                except mysql.connector.errors as eu:
                                    connection.rollback()
                                    logging.error(eu)
                                except AttributeError as ae:
                                    logging.error(ae)
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
                        if  StatusHilo == False:
                            Mantener_sesion = threading.Thread(name="Mantener-Sesion", target=MantenerSesion, args=(
                                Select, driver, By, logging, NoSuchWindowException, InvalidSessionIdException,
                                WebDriverException, EnvioCorreo,
                                NoSuchElementException))
                            Mantener_sesion.start()
                            rx.set('Stop_hilo', 0)
                    else:
                        logging.warning("El numero de cuenta no existe - " + str(x[1]))
                        id_estado = 6
                        Estados_trabajos(connection, logging, mysql, id_trabajo, nombre_cuenta, id_estado)
                        id_transaccion = str(x[0])
                        cola_de_trabajo(id_transaccion)
                        EnvioCorreo("El numero de cuenta no existe - " + str(x[1]))

    except NoSuchElementException as NSEE:
        logging.error("Problemas al cargar el sitio principal, se reinicia el servicio: "+str(NSEE))
        driver.get(os.getenv('CERRAR_SESION'))
        time.sleep(2)
        EnvioCorreo("Problemas al cargar el sitio, SE REINICIA EL SERVICIO")
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






