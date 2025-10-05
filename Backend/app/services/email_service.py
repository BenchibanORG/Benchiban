def send_reset_password_email(email: str, token: str):
 
    reset_link = f"http://localhost:3000/reset-password?token={token}"
    
    print("--- SIMULAÇÃO DE ENVIO DE EMAIL ---")
    print(f"Para: {email}")
    print("Assunto: Redefinição de Senha")
    print(f"Corpo: Por favor, clique no link a seguir para redefinir sua senha:")
    print(reset_link)
    print("------------------------------------")
    
    return True
