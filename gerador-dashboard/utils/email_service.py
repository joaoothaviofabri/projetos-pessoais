import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def enviar_email(destino, link):

    email_remetente = os.getenv("EMAIL_REMETENTE")
    senha_app = os.getenv("EMAIL_SENHA")

    msg = EmailMessage()
    msg["Subject"] = "Recuperação de Senha"
    msg["From"] = email_remetente
    msg["To"] = destino

    msg.set_content(f"""
Olá,

Recebemos uma solicitação para redefinir a sua senha.

Para continuar, clique no link abaixo:

{link}

Este link é válido por 15 minutos. Após esse período, será necessário solicitar uma nova redefinição.

Se você não solicitou essa alteração, pode ignorar este email com segurança.
""")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(email_remetente, senha_app)
            smtp.send_message(msg)

            print("Email enviado com sucesso.")

    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        print(email_remetente)
        print(senha_app)