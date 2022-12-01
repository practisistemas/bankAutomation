import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv


load_dotenv()

def EnvioCorreo(Mensaje):
    message = Mail(
        from_email='a.zapata@practisistemas.com',
        #to_emails=['a.zapata@practisistemas.com', 's.barrero@practisistemas.com', 'j.correal@practisistemas.com', 'd.guecha@practisistemas.com'],
        to_emails=['a.zapata@practisistemas.com', 'zapatasebastian306@gmail.com'],
        subject='Fallo servicio Bancolombia',
        html_content='<strong>'+ Mensaje+'</strong>')

    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)

