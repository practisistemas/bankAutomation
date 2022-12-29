import os
from datetime import datetime, timedelta
from datetime import date
from SendEmail import EnvioCorreo

def Notificacopnes(driver, Mensaje, logging, main):
    hoy = date.today()
    hora_actual = datetime.now()
    folio_number = str(hoy) + "-" + str(hora_actual.hour) + "-" + str(
        hora_actual.minute) + "-" + str(
        hora_actual.second) + str(".png")
    ruta = str(os.getcwd()) + "/Screenshot/"
    driver.get_screenshot_as_file(os.getcwd() + "/Screenshot/" + str(folio_number))

    Mensaje = "Se cerro el navegador inesperadamente, se encontraba en la ventana de login "
    logging.error(Mensaje )
    driver.close()
    EnvioCorreo(Mensaje, ruta, folio_number)
    logging.warning("Se reinicio el servico...")
    main()