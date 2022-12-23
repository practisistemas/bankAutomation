import os
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (Mail, Attachment, FileContent, FileName, FileType, Disposition)
from dotenv import load_dotenv



load_dotenv()

def EnvioCorreo(Mensaje, ruta,folio_number):
    message = Mail(
        from_email='a.zapata@practisistemas.com',
        #to_emails=['a.zapata@practisistemas.com', 'j.correal@practisistemas.com', 'd.guecha@practisistemas.com', 'zapatasebastian306@gmail.com'],
        to_emails=['a.zapata@practisistemas.com', 'zapatasebastian306@gmail.com'],
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

