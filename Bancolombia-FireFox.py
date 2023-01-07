# Librerias
import logging
import time
import threading
import os
import mysql
import pandas as pd
import selenium
import redis
import re
import urllib3

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
from datetime import datetime
from datetime import date
from ConexionRedis import ConexRedis


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
    # Conexion REDIS
    rx = ConexRedis.ConRedis(logging, EnvioCorreo, driver)

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
        EnvioCorreo(Mensaje, driver)
        logging.error(Mensaje + str(toe))
        driver.close()
        logging.warning("Se reinicio el servico...")
        main()

    except NoSuchWindowException as nswe:
        Mensaje = "Se cerro el navegador inesperadamente, se encontraba en la ventana de login "
        EnvioCorreo(Mensaje, driver)
        logging.error(Mensaje + str(nswe))
        driver.close()
        logging.warning("Se reinicio el servico...")
        main()

    except UnexpectedAlertPresentException as uape:
        Mensaje = "La información ingresada es incorrecta falta completar algun campo - " +str(uape)
        EnvioCorreo(Mensaje, driver)
        logging.error(Mensaje)


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
        EnvioCorreo(Mensaje, driver)
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
            element = driver.find_element(By.ID, 'el1')
            actions = ActionChains(driver)
            actions.move_to_element(element).perform()
            driver.switch_to.default_content()
            driver.switch_to.frame(1)
            element = driver.find_element(By.ID, 'pTR21').click()
            logging.info("INGRESO AL LISTADO DE CUENTAS...")

        except NoSuchElementException:
            Mensaje = "No se pudo desplegar el menu despues del inicio de sesion, SE REINICIA EL SERVICIO"
            EnvioCorreo(Mensaje, driver)
            logging.error("No se pudo desplegar el menu despues del inicio de sesion, SE REINICIA EL SERVICIO")
            driver.get(os.getenv('CERRAR_SESION'))
            time.sleep(2)
            driver.close()
            main()

        # conexion REDIS
        try:
            #rx = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=os.getenv('REDIS_DB'))
            # Hilo que hace movimientos en la pantalla para evitar cerrra sesion
            # Variable para romper el hilo
            # 1. se elimina la variable para evitar problemas de comunicacion

            rx.delete('Stop_hilo')
            # 2. se crea la variable
            rx.set('Stop_hilo', 0)
        except:
            logging.error("No se puede establecer una conexión ya que el equipo de destino denegó expresamente dicha conexión.")
            Mensaje = "Redis: No se puede establecer una conexión ya que el equipo de destino denegó expresamente dicha conexión."
            EnvioCorreo(Mensaje, driver)

        # Se crea Hilo y se inicializa
        Mantener_sesion = threading.Thread(name="Mantener-Sesion", target=MantenerSesion, args=(
        Select, driver, By, logging, NoSuchWindowException, WebDriverException, EnvioCorreo,NoSuchElementException, rx))
        Mantener_sesion.start()
        logging.info("SE INICIA HILO QUE MANTIENE LA SESION ABIERTA")

        # Inicia iteraciones con WHILE
        while True:
            TransaccionNueva = rx.get('TransaccionNueva')
            if str(TransaccionNueva) == '0':
                ValidaTransaccionNueva=0
            else:
                ValidaTransaccionNueva = 1

            #Cuenta la cantidad de trabajos con ESTADO = 1
            if(ValidaTransaccionNueva==0):
                # Verificar si existen elementos en este caso lista desplegable
                try:
                    element = driver.find_elements(By.NAME, 'accountList')
                    if element:
                        ExisteLista = 0
                    else:
                        ExisteLista = 1
                except:
                    ExisteLista = 1

                #Valida si se encuentra la lista desblegable donde se seleccionan las cuentas
                if ExisteLista==0:
                    rx.set('Stop_hilo', 0)
                else:
                    Mensaje = "Error: Hilo que mantiene la sesion abierta no encontro lista de cuentas, SE REINICIA EL SERVICIO"
                    EnvioCorreo(Mensaje, driver)
                    logging.error("Hilo que mantiene la sesion abierta no encontro lista de cuentas, SE REINICIA EL SERVICIO")
                    rx.set('Stop_hilo', 2)
                    #Funcion que valida si esta corriendo oo no el aplicativo
                    StatusRun(driver, By, logging, EnvioCorreo, NoSuchElementException, WebDriverException, 2, rx)
                    driver.get(os.getenv('CERRAR_SESION'))
                    time.sleep(10)
                    driver.quit()
                    time.sleep(5)
                    main()
            else:
                logging.info("Se encontraron transacciones nuevas")
                rx.set('Stop_hilo', 1)
                rx.set('TransaccionNueva',0)
                try:
                    global MyCursor0
                    if connection.is_connected():
                        print("Peticion recibida")
                    else:
                        connection.reconnect()
                    MyCursor0 = connection.cursor()
                    MyCursor0.execute("SELECT * FROM trabajo WHERE estado = 1 ")
                    MyResult = MyCursor0.fetchall()
                except mysql.connector.Error as error:
                    logging.error(error)
                    print("Error")
                finally:
                    MyCursor0.close()

                # Ingresar cuenta por cuenta
                for x in MyResult:
                    id_trabajo = str(x[0])
                    nombre_cuenta = str(x[1])
                    ExisteCuenta=1
                    try:
                        dropdown_element = driver.find_element(By.NAME, 'accountList')
                        selected_value = dropdown_element.get_attribute("value")
                        value_get = selected_value.split("|")
                        value_text = value_get[0]
                        if str(value_text) == nombre_cuenta:
                            element_list=[]
                            dropdown_element_0 = driver.find_elements(By.NAME, 'accountList')
                            for option in dropdown_element_0:
                                text = option.get_attribute("innerHTML")
                                pattern = r'value="[^"]*">'   # Expresión regular para buscar texto entre símbolos menor que y mayor que
                            for match in re.finditer(pattern, text):
                                cadena = match.group()
                                cadena_izquierda = cadena.lstrip('value="')
                                cadena_final = cadena_izquierda.rstrip('">')
                                value_item = cadena_final.split("|")
                                text_final = value_item[0]
                                element_list.append(text_final)
                            element_list.remove("")
                            position_elemet = element_list.index(nombre_cuenta)
                            if position_elemet == len(element_list):
                                element_to_select = position_elemet- (position_elemet+1)
                            else:
                                element_to_select = position_elemet+1

                            select_1 = Select(driver.find_element(By.NAME, 'accountList'))
                            Nom_cuenta= "BANCOLOMBIA - Ahorros - "+ str(element_list[element_to_select])
                            select_1.select_by_visible_text(str(Nom_cuenta))
                            print("cuenta 1: " + Nom_cuenta)
                            time.sleep(1)
                            select_2 = Select(driver.find_element(By.NAME, 'accountList'))
                            print("Nombre cuenta Default: "+str(nombre_cuenta))
                            Nom_cuenta_1= "BANCOLOMBIA - Ahorros - "+ str(nombre_cuenta)
                            select_2.select_by_visible_text(str(Nom_cuenta_1))
                            print("cuenta 2" + Nom_cuenta_1)

                        else:
                            # Despliega la lista donde se encuentran las cuentas
                            select = Select(driver.find_element(By.NAME, 'accountList'))
                            Nom_cuenta= "BANCOLOMBIA - Ahorros - "+ str(nombre_cuenta)
                            select.select_by_visible_text(str(Nom_cuenta))

                    except NoSuchElementException:
                        ExisteCuenta = 0
                    except:
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
                            logging.info("Existen transacciones en la cuenta: " + str(nombre_cuenta))
                            # Extrae informacion de las tablas y numero de columnas y filas
                            cols = driver.find_elements(By.XPATH, '/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr[4]/td')
                            #rows = driver.find_elements(By.XPATH, '/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr')
                            rows = driver.find_elements(By.XPATH,'/html/body/table/tbody/tr/td/div/form[3]/table[2]/tbody/tr[4]/td/table/tbody/tr')

                            rows1 = 1 + len(rows)

                            logging.info("Total de Filas" + str(rows1))

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
                                else:
                                    print("Transacciones descartadas ")
                            logging.info(df)

                            # Crea tabla para almacenar los registros
                            ### optiene las ultimas 20 transaciones de la cuenta
                            dia = date.today()
                            global  result_SQL
                            try:
                                MyCursor2 = connection.cursor()
                                sql6 = "SELECT Hora FROM tiempo_real WHERE Fecha= %s AND Cuenta = %s  ORDER BY Id DESC LIMIT 1"
                                val6 = (dia, str(nombre_cuenta))
                                MyCursor2.execute(sql6, val6)
                                result_SQL = MyCursor2.fetchone()
                            except mysql.connector.Error as error:
                                logging.error(error)
                                print(f"Error: {error}")
                            finally:
                                MyCursor2.close()

                            pos = []
                            guardar = 0
                            cont = 0
                            if result_SQL == None:
                                for k in range(len(df["valor"])):
                                    today = date.today()
                                    d1 = today.strftime("%Y/%m/%d")
                                    if str(df.loc[k, "fecha"]).strip() == str(d1).strip():
                                        pos.append(k)
                                        guardar += 1
                            else:
                                #for k in df["hora"]:
                                for k, y in zip(df["hora"], df["fecha"]):
                                    result = re.sub('[^0-9:]', '', k)
                                    hora1 = datetime.strptime(result, '%H:%M:%S').time()
                                    hora2 = datetime.strptime(str(result_SQL[0]), '%H:%M:%S').time()
                                    today = date.today()
                                    d1 = today.strftime("%Y/%m/%d")

                                    if  hora1 > hora2 and str(y).strip() == str(d1).strip():
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
                                            df.loc[i, "oficina"], df.loc[i, "saldo_canje"], df.loc[i, "valor"], str(nombre_cuenta), str(id_trabajo)))
                                    MyCursor3.executemany(sql1, val1)
                                    connection.commit()
                                    cont += 1

                                except mysql.connector.errors.ProgrammingError as error:
                                    connection.rollback()
                                    logging.error("No se insertaron registros de la cuenta " + str(nombre_cuenta))
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
                                logging.warning("No se registraron pagos nuevos en la cuenta " + str(nombre_cuenta))
                                id_estado = 4
                                Estados_trabajos(connection, logging, mysql, id_trabajo, nombre_cuenta, id_estado)
                                id_transaccion= str(id_trabajo)
                                cola_de_trabajo(id_transaccion, rx)
                            else:
                                #Se actualiza el estado a 1 EXISTEN NUEVOS PAGOS
                                logging.warning("Se registraron pagos a la cuenta" + str(nombre_cuenta))
                                id_estado = 2
                                Estados_trabajos(connection, logging, mysql, id_trabajo, nombre_cuenta, id_estado)
                                id_transaccion = str(id_trabajo)
                                cola_de_trabajo(id_transaccion, rx)

                        else:
                            # Actualiza el estado del trabajo a ESTADO = 2 para no ser procesado de nuevo
                            logging.warning("No existen registros que cumplan con el criterio de búsqueda seleccionado - " + str(x[1]))
                            id_estado = 3
                            Estados_trabajos(connection,logging,mysql,id_trabajo,nombre_cuenta,id_estado)
                            id_transaccion = str(id_trabajo)
                            cola_de_trabajo(id_transaccion, rx)

                        # Se termina de realizar la extraccion de la informacion y se reaunda el Hilo
                        StatusHilo = Mantener_sesion.is_alive()
                        print("Status hilo: "+ str(StatusHilo))
                        rx.set('Stop_hilo', 0)

                    else:
                        logging.warning("El numero de cuenta no existe - " + str(nombre_cuenta))
                        id_estado = 6
                        Estados_trabajos(connection, logging, mysql, id_trabajo, nombre_cuenta, id_estado)
                        id_transaccion = str(x[0])
                        cola_de_trabajo(id_transaccion, rx)
                        Mensaje = "El numero de cuenta no existe - " + str(nombre_cuenta)
                        #EnvioCorreo(Mensaje, driver)
                        rx.set('Stop_hilo', 0)

    except NoSuchElementException as NSEE:
        Mensaje = "Problemas al cargar el sitio, SE REINICIA EL SERVICIO"
        EnvioCorreo(Mensaje, driver)
        logging.error("Problemas al cargar el sitio principal, SE REINICIA EL SERVICIO "+str(NSEE))
        driver.get(os.getenv('CERRAR_SESION'))
        time.sleep(2)
        rx.set('Stop_hilo', 2)
        driver.close()
        main()

    except MoveTargetOutOfBoundsException as MTOBE:
        Mensaje = "Problemas al desplegar el menu, SE REINICIA EL SERVICIO " + str(MTOBE)
        EnvioCorreo(Mensaje, driver)
        logging.error("Problemas al desplegar el menu, SE REINICIA EL SERVICIO "+ str(MTOBE))
        driver.get(os.getenv('CERRAR_SESION'))
        time.sleep(2)
        rx.set('Stop_hilo', 2)
        driver.close()
        main()


    except WebDriverException as WD:
        Mensaje = "Se cerro inesperadamente el navegador, SE REINICIA EL SERVICIO "+ str(WD)
        EnvioCorreo(Mensaje, driver)
        logging.error("Se cerro inesperadamente el navegador, SE REINICIA EL SERVICIO "+ str(WD))
        rx.set('Stop_hilo', 2)
        driver.close()
        main()

    except InvalidSessionIdException as IE:
        Mensaje = "Se detuvo el hilo de sesion inesperadamente, SE REINICIA EL SERVICIO " + str(IE)
        EnvioCorreo(Mensaje, driver)
        logging.error("Se detuvo el hilo de sesion inesperadamente, SE REINICIA EL SERVICIO " + str(IE))
        driver.get(os.getenv('CERRAR_SESION'))
        time.sleep(2)
        rx.set('Stop_hilo', 2)
        driver.quit()
        time.sleep(5)
        main()




if __name__ =="__main__":
    main()






