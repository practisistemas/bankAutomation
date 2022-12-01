# Librerias
import logging
import time
import threading
import os


import mysql
import selenium
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
from Hilos import MantenerSesion, CerrarSesion
from dotenv import load_dotenv
from Estados import Estados_trabajos
from Trabajos import  cola_de_trabajo
from SendEmail import EnvioCorreo
import redis



# load_dotenv = Optiene los resultados de las variables de entorno
load_dotenv()
#Configuracion log
#%(threadName)s - %(processName)s -
"""logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        filename='bancolombia.log',
                        filemode='a')"""

def main():
    #Configuracion navegador
    options = Options()
    options.headless = False
    driver = webdriver.Firefox()
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
        Mensaje= "No se pudo iniciar sesion, datos de ingreso incorrectos, problemas con el servicio de bancolombia o usuario bloqueado, EL SERVICIO QUEDA DETENIDO HASTA NO VALIDAR EL FALLO"
        logging.error(Mensaje)
        EnvioCorreo(Mensaje)
        driver.close()
    else:
        logging.info("INICIO DE SESION EXITOSO")

    #Inicia proceso para acceder al listado de cuentas y transacciones
    try:
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

        # Inicia iteraciones con WHILE
        while True:
            # Consultas todas las solicitudes en la cola de trabajo con ESTADO = 1
            try:
                MyCursor = connection.cursor()
                MyCursor.execute("SELECT * FROM trabajo WHERE estado = 1 ")
                MyResult = MyCursor.fetchall()
            finally:
                MyCursor.close()

        #Cuenta la cantidad de trabajos con ESTADO = 1
            if(len(MyResult)==0):
                # conexion REDIS
                rx = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=os.getenv('REDIS_DB'))
                # Variable para romper el hilo
                # 1. se elimina la variable para evitar problemas de comunicacion
                rx.delete('Stop_hilo')
                # 2. se crea la variable
                rx.set('Stop_hilo', 0)

                #Hilo que hace movimientos en la pantalla para evitar cerrra sesion
                Mantener_sesion = threading.Thread(name="Mantener-Sesion", target=MantenerSesion, args=(Select, driver, By, logging, NoSuchWindowException, InvalidSessionIdException, WebDriverException, EnvioCorreo, NoSuchElementException))
                Mantener_sesion.start()
                logging.info("SE INICIA HILO QUE MANTIENE LA SESION ABIERTA")

                while True:
                    # Consulta el total de solicitudes en la cola de trabajo
                    try:
                        connection.autocommit = True
                        MyCursor = connection.cursor()
                        MyCursor.execute("SELECT COUNT(Id) FROM trabajo WHERE estado = 1 ")
                        MyResult4 = MyCursor.fetchone()
                    finally:
                        MyCursor.close()
                    time.sleep(1)
                    if (MyResult4[0] >= 1):
                        logging.info("Se encontraron transacciones nuevas")
                        rx.set('Stop_hilo', 1)
                        #Rompe el bucle para realizar la condicion
                        break
                    else:
                        #Variable para validar si la lista desplegable donde se encuentran las cuentas existe o se encuentra en otra ventana
                        ExisteLista=0
                        try:
                            driver.find_element(By.NAME, 'accountForDetail').is_displayed()
                        except selenium.common.exceptions.NoSuchElementException:
                            ExisteLista = 1

                        if ExisteLista==0:
                            logging.warning("Esperando por transacciones...")
                            rx.set('Stop_hilo', 0)
                        else:
                            logging.error("Hilo que mantiene la sesion abierta no encontro lista de cuentas, se reinicia el servicio")
                            rx.set('Stop_hilo', 1)
                            driver.get(os.getenv('CERRAR_SESION'))
                            time.sleep(2)
                            EnvioCorreo("Error: Hilo que mantiene la sesion abierta no encontro lista de cuentas, se reinicia el servicio")
                            driver.close()
                            main()

            else:
                # Ingresar cuenta por cuenta
                for x in MyResult:
                    id_trabajo = str(x[0])
                    nombre_cuenta = str(x[1])

                    # Despliega la lista donde se encuentran las cuentas
                    select = Select(driver.find_element(By.NAME, 'accountForDetail'))
                    Nom_cuenta= "BANCOLOMBIA - Ahorros - "+ str(x[1])
                    select.select_by_visible_text(str(Nom_cuenta))
                    # Espera 2 segundos
                    time.sleep(2)

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
                        cols1 = len(cols)

                        #Contador para validar si la cuenta no tiene pagos nuevos para procesar
                        cont = 0
                        for r in range(1, rows1):
                            fecha = driver.find_element(By.XPATH,"/html/body/div[43]/p[2]/table[1]/tbody/tr[" + str(r) + "]/td[1]").text
                            descripcion = driver.find_element(By.XPATH,"/html/body/div[43]/p[2]/table[1]/tbody/tr[" + str(r) + "]/td[2]").text
                            sucursal = driver.find_element(By.XPATH, "/html/body/div[43]/p[2]/table[1]/tbody/tr[" + str(r) + "]/td[3]").text
                            referencia_1 = driver.find_element(By.XPATH,"/html/body/div[43]/p[2]/table[1]/tbody/tr[" + str(r) + "]/td[4]").text
                            referencia_2 = driver.find_element(By.XPATH, "/html/body/div[43]/p[2]/table[1]/tbody/tr[" + str(r) + "]/td[5]").text
                            documento = driver.find_element(By.XPATH, "/html/body/div[43]/p[2]/table[1]/tbody/tr[" + str(r) + "]/td[6]").text
                            valor = driver.find_element(By.XPATH,"/html/body/div[43]/p[2]/table[1]/tbody/tr[" + str(r) + "]/td[7]").text

                            # Valida si el documento viene vacio
                            documentoFinal = documento.strip()
                            if(documentoFinal == ''):
                                documento = 0

                            ## Falta validar que traiga solo numeros

                            #quita las , del valor  y los espacios en blanco al inicio y al final de valor
                            valorPreliminar = valor.replace(",", "")
                            valorFinal = valorPreliminar.strip()


                            referencia_1_1 = referencia_1.strip()
                            referencia_2_2 = referencia_2.strip()

                            #Valida si los datos ya se encuentran registrados
                            try:
                                MyCursor = connection.cursor()
                                sql0 = "SELECT COUNT(Id) FROM tiempo_real WHERE Fecha = %s  AND  Referencia_1 = %s AND  Referencia_2 = %s AND Cuenta = %s AND Valor = %s"
                                val0 = (fecha, referencia_1_1, referencia_2_2, str(x[1]),valorFinal)
                                MyCursor.execute(sql0, val0)
                                Existe = MyCursor.fetchone()
                            finally:
                                MyCursor.close()

                            if (Existe[0] >=1):
                                logging.info("La transaccion ya existe: " +descripcion +"  "+referencia_1_1+"  "+referencia_2_2+ "     "+str(x[1])+"     "+valorFinal)
                            else:
                                #Inserta los registros en la base de datos
                                try:
                                    MyCursor = connection.cursor()
                                    sql1 = "INSERT INTO tiempo_real(Fecha, Descripcion, Sucursal_canal, Referencia_1, Referencia_2, Documento, Valor, Cuenta, Id_trabajo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                                    val1 = (fecha, descripcion, sucursal, referencia_1_1, referencia_2_2, documento, valorFinal, str(x[1]), str(x[0]))
                                    MyCursor.execute(sql1, val1)
                                    connection.commit()
                                    cont += 1

                                except mysql.connector.errors.ProgrammingError as error:
                                    connection.rollback()
                                    logging.error("No se insertaron registros de la cuenta "+str(x[1]))
                                except mysql.connector.errors as eu:
                                    connection.rollback()
                                    logging.error(eu)
                                except AttributeError as ae:
                                    logging.error(ae)
                                finally:
                                    MyCursor.close()

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






