import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

EMAIL_ORIGEN = os.environ.get("EMAIL_ORIGEN")            
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")        
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))

def enviar_correo(destinatario: str, asunto: str, mensaje: str, es_html: bool = False) -> bool:
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ORIGEN
        msg['To'] = destinatario
        msg['Subject'] = asunto

        cuerpo = MIMEText(mensaje, 'html' if es_html else 'plain')
        msg.attach(cuerpo)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ORIGEN, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ORIGEN, destinatario, msg.as_string())

        print(f"[✅] Correo enviado a {destinatario}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[❌] Error de autenticación: verifica tu contraseña de aplicación.")
        return False

    except smtplib.SMTPConnectError:
        print("[❌] Error de conexión con el servidor SMTP.")
        return False

    except Exception as e:
        print(f"[❌] Error inesperado: {e}")
        return False

def enviar_alerta_presupuesto(correo: str, categoria: str, monto_gastado: float, porcentaje: float):
    asunto = "⚠️ Alerta de Presupuesto Excedido"
    mensaje = f"""
    Hola,<br><br>
    Has superado el presupuesto mensual para la categoría <strong>{categoria}</strong>.<br>
    Total gastado: <strong>${monto_gastado:.2f}</strong><br>
    Porcentaje: <strong>{porcentaje:.1f}%</strong><br><br>
    Revisa tus gastos para evitar sobrepasar tu límite.
    """
    return enviar_correo(correo, asunto, mensaje, es_html=True)
