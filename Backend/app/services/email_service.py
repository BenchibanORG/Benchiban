import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.core.config import settings

def send_reset_password_email(email_to: str, token: str):
    """
    Envia um e-mail de redefinição de senha usando a API do SendGrid.
    """
    link = f"http://localhost:3000/reset-password?token={token}"
    
    message = Mail(
        from_email=settings.EMAILS_FROM_EMAIL,
        to_emails=email_to,
        subject='Benchiban - Redefinição de Senha',
        html_content=f"""
            <div style="font-family: sans-serif; text-align: center; padding: 20px;">
                <h2 style="color: #333;">Solicitação de Redefinição de Senha</h2>
                <p>Olá,</p>
                <p>Recebemos uma solicitação para redefinir a senha da sua conta.</p>
                <p>Por favor, clique no botão abaixo para criar uma nova senha. Este link é válido por 15 minutos.</p>
                <a href="{link}" style="background-color: #007bff; color: white; padding: 15px 25px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; margin: 20px 0;">
                    Redefinir Minha Senha
                </a>
                <p>Se você não solicitou esta alteração, pode ignorar este e-mail com segurança.</p>
            </div>
        """
    )
    
    try:
        sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sendgrid_client.send(message)
        
        # Verifica se a API do SendGrid realmente aceitou o e-mail
        if response.status_code >= 200 and response.status_code < 300:
            logging.info(f"E-mail de redefinição enviado para {email_to}, status: {response.status_code}")
        else:
            # Se não, regista o erro exato retornado pelo SendGrid
            logging.error(f"Falha ao enviar e-mail para {email_to}. SendGrid respondeu com status {response.status_code}.")
            logging.error(f"Corpo da resposta do SendGrid: {response.body}")
        
        return response
        
    except Exception as e:
        # Regista qualquer outra exceção que possa ocorrer (ex: erro de rede)
        logging.error(f"Exceção ao tentar enviar e-mail para {email_to} via SendGrid: {e}")
        raise