from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
import json
import uvicorn

app = FastAPI(title="AIuda WhatsApp Bot", version="1.0.0")

# Cargar configuración del menú
def cargar_menu():
    try:
        with open("menu.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ ERROR: No se encuentra menu.json")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ ERROR en menu.json: {e}")
        return None

# Formatear menú para WhatsApp
def formatear_menu_whatsapp():
    menu = cargar_menu()
    if not menu:
        return "Error al cargar el menú. Por favor contacta al administrador."
    
    mensaje = menu["bienvenida"] + "\n\n"
    mensaje += menu["menu_principal"]["titulo"] + "\n\n"
    
    for opcion in menu["menu_principal"]["opciones"]:
        mensaje += f"{opcion['emoji']} *{opcion['id']}*. {opcion['nombre']}\n"
    
    mensaje += "\n_Escribe el número de la opción que prefieras._"
    return mensaje

# Procesar mensaje del usuario
def procesar_mensaje(texto_usuario):
    menu = cargar_menu()
    if not menu:
        return "Error del sistema. Por favor intenta más tarde."
    
    texto = texto_usuario.strip()
    
    # Comandos especiales
    if texto.lower() in ["hola", "inicio", "menu", "start", "hi", "hello"]:
        return formatear_menu_whatsapp()
    
    # Ayuda urgente por palabras clave
    if texto.lower() in ["urgente", "ayuda", "sos", "emergency", "emergencia", "auxilio"]:
        return menu["ayuda_urgente"]["mensaje"]
    
    # Selección por número
    try:
        opcion_num = int(texto)
        opciones = menu["menu_principal"]["opciones"]
        
        for opcion in opciones:
            if opcion["id"] == opcion_num:
                # Caso especial: Ayuda urgente
                if opcion["categoria"] == "urgente":
                    return menu["ayuda_urgente"]["mensaje"]
                
                # Respuesta para otras categorías
                respuesta = f"{opcion['emoji']} *{opcion['nombre']}*\n\n"
                respuesta += f"{opcion['descripcion']}\n\n"
                respuesta += "_Preparando la técnica..._\n\n"
                respuesta += "Escribe *menu* para volver al inicio."
                return respuesta
        
        # Número fuera de rango
        return "❌ Opción no válida. Por favor elige un número del 1 al 6.\n\nEscribe *menu* para ver las opciones."
    
    except ValueError:
        # No es un número
        return "No entendí tu mensaje. 🤔\n\nEscribe *menu* para ver las opciones disponibles."

# Endpoint raíz
@app.get("/")
def root():
    return {
        "status": "✅ AIuda WhatsApp Bot funcionando",
        "version": "1.0.0",
        "webhook": "/whatsapp",
        "instrucciones": "Configura este endpoint en Twilio Sandbox"
    }

# Endpoint principal de WhatsApp
@app.post("/whatsapp")
async def whatsapp_webhook(
    Body: str = Form(...),
    From: str = Form(...),
    ProfileName: str = Form(None)
):
    """Recibe mensajes de WhatsApp vía Twilio y responde"""
    
    try:
        # Log del mensaje recibido
        print(f"\n{'='*60}")
        print(f"📩 Mensaje recibido")
        print(f"   De: {ProfileName} ({From})")
        print(f"   Texto: {Body}")
        print(f"{'='*60}")
        
        # Procesar el mensaje
        respuesta_texto = procesar_mensaje(Body)
        
        # Log de la respuesta
        print(f"📤 Respuesta generada:")
        print(f"   {respuesta_texto[:150]}{'...' if len(respuesta_texto) > 150 else ''}")
        
        # Crear respuesta en formato TwiML
        resp = MessagingResponse()
        resp.message(respuesta_texto)
        
        # Convertir a XML
        xml_response = str(resp)
        print(f"📋 XML enviado: {xml_response[:200]}...")
        print(f"{'='*60}\n")
        
        # Retornar respuesta con el tipo de contenido correcto
        return Response(content=xml_response, media_type="application/xml")
    
    except Exception as e:
        # Log de error detallado
        print(f"\n{'='*60}")
        print(f"❌ ERROR en webhook")
        print(f"   Mensaje: {e}")
        print(f"{'='*60}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        # Respuesta de error para el usuario
        resp = MessagingResponse()
        resp.message("Lo siento, hubo un error técnico. 😔\n\nEscribe *menu* para intentar de nuevo.")
        return Response(content=str(resp), media_type="application/xml")

# Endpoint de prueba (opcional)
@app.get("/test")
def test_menu():
    """Endpoint para probar el menú sin WhatsApp"""
    return {
        "menu": formatear_menu_whatsapp(),
        "test_responses": {
            "hola": procesar_mensaje("hola"),
            "1": procesar_mensaje("1"),
            "6": procesar_mensaje("6")
        }
    }

# Ejecutar servidor
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Iniciando AIuda WhatsApp Bot")
    print("="*60)
    print("📍 Servidor: http://0.0.0.0:8000")
    print("🔗 Webhook: /whatsapp")
    print("📝 Asegúrate de que menu.json esté en la misma carpeta")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)