import os
import base64
import json
from datetime import datetime, timedelta
from datetime import date
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition)
from dotenv import load_dotenv
load_dotenv()


def EnvioCorreo(Mensaje,driver):

    print(driver)

    # Concatena hora y fecha para  Tomar captura de pantalla
    hoy = date.today()
    hora_actual = datetime.now()
    folio_number = str(hoy) + "-" + str(hora_actual.hour) + "-" + str(hora_actual.minute) + "-" + str(
        hora_actual.second) + str(".png")
    ruta = str(os.getcwd()) + "/Screenshot/"
    driver.get_screenshot_as_file(os.getcwd() + "/Screenshot/" + str(folio_number))

    correos_not = json.loads(os.environ['CORREO_NOTIFICACION'])
    message = Mail(
        from_email=os.environ['FROM_EMAIL'],
        to_emails=correos_not,
        subject='Fallo - servicio Bancolombia',
        html_content= Mensaje)

    Origen = str(ruta)+str(folio_number)
    with open(Origen, 'rb') as f:
        data = f.read()
        f.close()
    encoded_file = base64.b64encode(data).decode()

    attachedFile = Attachment(
        FileContent(encoded_file),
        FileName(folio_number),
        FileType('application/png'),
        Disposition('attachment')
    )
    message.attachment = attachedFile

    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        print('CORREO ENVIADO')
        """print(response.status_code)
        print(response.body)
        print(response.headers)"""
    except Exception as e:
        print(e.message)

