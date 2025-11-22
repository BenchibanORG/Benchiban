
import pytest
from unittest.mock import patch, Mock, MagicMock
from app.services.email_service import send_reset_password_email


class TestSendResetPasswordEmail:
    """Testes para a função de envio de email de reset"""
    
    @patch('app.services.email_service.SendGridAPIClient')
    def test_send_reset_email_success(self, mock_sendgrid_client):
        """
        Dado: Email e token válidos
        Quando: Envio email de reset
        Então: Email é enviado com sucesso via SendGrid
        """
        # Arrange
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 202  # SendGrid success code
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance
        
        email = "user@example.com"
        token = "fake_reset_token_123"
        
        # Act
        response = send_reset_password_email(email_to=email, token=token)
        
        # Assert
        assert response.status_code == 202
        mock_client_instance.send.assert_called_once()
    
    @patch('app.services.email_service.SendGridAPIClient')
    def test_send_reset_email_constructs_correct_link(self, mock_sendgrid_client):
        """
        Dado: Um token de reset
        Quando: Construo o email
        Então: Link contém o token correto
        """
        # Arrange
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 202
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance
        
        email = "test@example.com"
        token = "my_special_token"
        
        # Act
        send_reset_password_email(email_to=email, token=token)
        
        # Assert
        # Verifica que o método send foi chamado
        call_args = mock_client_instance.send.call_args
        sent_message = call_args[0][0]
        
        # O link deve conter o token
        assert token in sent_message.contents[0].content
        assert "http://localhost:3000/reset-password?token=" in sent_message.contents[0].content
    
    @patch('app.services.email_service.SendGridAPIClient')
    def test_send_reset_email_correct_sender(self, mock_sendgrid_client):
        """
        Dado: Configurações de email
        Quando: Envio email
        Então: Usa o from_email correto das settings
        """
        # Arrange
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 202
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance
        
        from app.core.config import settings
        
        # Act
        send_reset_password_email(email_to="user@example.com", token="token123")
        
        # Assert
        call_args = mock_client_instance.send.call_args
        sent_message = call_args[0][0]
        
        assert sent_message.from_email.email == settings.EMAILS_FROM_EMAIL
    
    @patch('app.services.email_service.SendGridAPIClient')
    def test_send_reset_email_correct_recipient(self, mock_sendgrid_client):
        """
        Dado: Email do destinatário
        Quando: Envio email
        Então: Email é endereçado corretamente
        """
        # Arrange
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 202
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance
        
        recipient_email = "recipient@example.com"
        
        # Act
        send_reset_password_email(email_to=recipient_email, token="token123")
        
        # Assert
        call_args = mock_client_instance.send.call_args
        sent_message = call_args[0][0]
        
        # Verifica o destinatário
        assert sent_message.personalizations[0].tos[0]['email'] == recipient_email
    
    @patch('app.services.email_service.SendGridAPIClient')
    def test_send_reset_email_has_correct_subject(self, mock_sendgrid_client):
        """
        Dado: Email de reset sendo enviado
        Quando: Verifico o assunto
        Então: Assunto está correto
        """
        # Arrange
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 202
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance
        
        # Act
        send_reset_password_email(email_to="user@example.com", token="token")
        
        # Assert
        call_args = mock_client_instance.send.call_args
        sent_message = call_args[0][0]
        
        assert sent_message.subject.subject == 'Benchiban - Redefinição de Senha'
    
    @patch('app.services.email_service.SendGridAPIClient')
    def test_send_reset_email_sendgrid_failure(self, mock_sendgrid_client):
        """
        Dado: SendGrid retorna erro
        Quando: Tento enviar email
        Então: Exceção é propagada
        """
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.send.side_effect = Exception("SendGrid API Error")
        mock_sendgrid_client.return_value = mock_client_instance
        
        # Act & Assert
        with pytest.raises(Exception, match="SendGrid API Error"):
            send_reset_password_email(email_to="user@example.com", token="token")
    
    @patch('app.services.email_service.SendGridAPIClient')
    def test_send_reset_email_logs_failure(self, mock_sendgrid_client):
        """
        Dado: SendGrid retorna status de erro
        Quando: Envio email
        Então: Status de erro é registrado no log
        """
        # Arrange
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 400  # Bad Request
        mock_response.body = "Invalid API Key"
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance
        
        # Act
        with patch('app.services.email_service.logging') as mock_logging:
            response = send_reset_password_email(
                email_to="user@example.com", 
                token="token"
            )
            
            # Assert
            assert response.status_code == 400
            # Verifica se o erro foi logado
            assert mock_logging.error.called
    
    @patch('app.services.email_service.SendGridAPIClient')
    def test_send_reset_email_html_content_format(self, mock_sendgrid_client):
        """
        Dado: Email sendo construído
        Quando: Verifico o conteúdo HTML
        Então: Contém elementos esperados (botão, título, etc)
        """
        # Arrange
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 202
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance
        
        # Act
        send_reset_password_email(email_to="user@example.com", token="test_token")
        
        # Assert
        call_args = mock_client_instance.send.call_args
        sent_message = call_args[0][0]
        html_content = sent_message.contents[0].content
        
        # Verifica elementos importantes do HTML
        assert "Solicitação de Redefinição de Senha" in html_content
        assert "Redefinir Minha Senha" in html_content
        assert "<a href=" in html_content
        assert "válido por 15 minutos" in html_content
    
    @patch('app.services.email_service.SendGridAPIClient')
    def test_send_reset_email_multiple_recipients_separately(self, mock_sendgrid_client):
        """
        Dado: Múltiplos emails sendo enviados
        Quando: Envio para diferentes usuários
        Então: Cada email tem seu próprio token
        """
        # Arrange
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 202
        mock_client_instance.send.return_value = mock_response
        mock_sendgrid_client.return_value = mock_client_instance
        
        # Act
        send_reset_password_email(email_to="user1@example.com", token="token1")
        send_reset_password_email(email_to="user2@example.com", token="token2")
        
        # Assert
        assert mock_client_instance.send.call_count == 2
        
        # Verifica que os tokens são diferentes em cada chamada
        call1 = mock_client_instance.send.call_args_list[0][0][0]
        call2 = mock_client_instance.send.call_args_list[1][0][0]
        
        assert "token1" in call1.contents[0].content
        assert "token2" in call2.contents[0].content