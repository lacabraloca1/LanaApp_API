import os

TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.environ.get("TWILIO_FROM")

def enviar_sms(destino: str, mensaje: str) -> bool:
    """Envía SMS vía Twilio. Devuelve True si se envió, False si no está configurado o falló."""
    if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and destino):
        return False
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(to=destino, from_=TWILIO_FROM, body=mensaje)
        return True
    except Exception as e:
        print(f"[SMS] Error enviando SMS a {destino}: {e}")
        return False
