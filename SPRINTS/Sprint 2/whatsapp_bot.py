from fastapi import FastAPI, Form, Request, BackgroundTasks
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import json
import uvicorn
import asyncio
import os

app = FastAPI(title="AIuda WhatsApp Bot", version="2.1.0")

# Configuración de Twilio (necesaria para enviar mensajes automáticos)
# IMPORTANTE: Agrega estas variables de entorno o configúralas directamente
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

# Cliente de Twilio para enviar mensajes proactivos
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Almacenamiento de sesiones en memoria
sesiones_usuario = {}

# Cargar configuraciones
def cargar_json(archivo):
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: No se encuentra {archivo}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ ERROR en {archivo}: {e}")
        return None

def cargar_menu():
    return cargar_json("menu.json")

def cargar_ejercicios():
    return cargar_json("ejercicios.json")

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

# Gestión de sesiones
def obtener_sesion(user_id):
    if user_id not in sesiones_usuario:
        sesiones_usuario[user_id] = {
            "estado": "menu",
            "ejercicio_actual": None,
            "paso_actual": 0,
            "esperando_respuesta": False
        }
    return sesiones_usuario[user_id]

def actualizar_sesion(user_id, estado=None, ejercicio=None, paso=None, esperando=None):
    sesion = obtener_sesion(user_id)
    if estado is not None:
        sesion["estado"] = estado
    if ejercicio is not None:
        sesion["ejercicio_actual"] = ejercicio
    if paso is not None:
        sesion["paso_actual"] = paso
    if esperando is not None:
        sesion["esperando_respuesta"] = esperando
    return sesion

def reiniciar_sesion(user_id):
    sesiones_usuario[user_id] = {
        "estado": "menu",
        "ejercicio_actual": None,
        "paso_actual": 0,
        "esperando_respuesta": False
    }

# Enviar mensaje de WhatsApp proactivo
async def enviar_mensaje_whatsapp(destinatario, mensaje, delay=0):
    """Envía un mensaje de WhatsApp con un delay opcional"""
    if delay > 0:
        await asyncio.sleep(delay)
    
    if not twilio_client:
        print(f"⚠️ Twilio no configurado. Mensaje simulado: {mensaje[:50]}...")
        return
    
    try:
        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=mensaje,
            to=destinatario
        )
        print(f"✉️ Mensaje automático enviado a {destinatario}: {mensaje[:50]}...")
        return message
    except Exception as e:
        print(f"❌ Error al enviar mensaje: {e}")
        return None

# Ejecutar ejercicio de respiración automático
async def ejecutar_respiracion_automatica(destinatario):
    """Ejecuta el ejercicio de respiración con mensajes automáticos"""
    ejercicios = cargar_ejercicios()
    if not ejercicios or "respiracion" not in ejercicios:
        return
    
    pasos_respiracion = [
        (0, "Vamos a comenzar. Prepárate..."),
        (2, "Inhala profundamente por la nariz... 🌬️\n1... 2... 3... 4..."),
        (5, "Mantén el aire... ⏸️\n1... 2... 3... 4..."),
        (5, "Exhala lentamente por la boca... 💨\n1... 2... 3... 4... 5... 6..."),
        (3, "Muy bien 👏 Vamos con el segundo ciclo..."),
        (2, "Inhala profundamente... 🌬️\n1... 2... 3... 4..."),
        (5, "Mantén... ⏸️\n1... 2... 3... 4..."),
        (5, "Exhala... 💨\n1... 2... 3... 4... 5... 6..."),
        (3, "Último ciclo, lo estás haciendo genial..."),
        (2, "Inhala... 🌬️"),
        (5, "Mantén... ⏸️"),
        (5, "Exhala... 💨"),
        (3, "✨ Excelente trabajo ✨\n\n¿Cómo te sientes ahora?\n\nPuedes escribir cómo te sientes o escribe *menu* para volver.")
    ]
    
    for delay, mensaje in pasos_respiracion:
        await enviar_mensaje_whatsapp(destinatario, mensaje, delay)
    
    # Marcar ejercicio como completado
    actualizar_sesion(destinatario, estado="esperando_feedback", esperando=True)

# Ejecutar ejercicio de grounding interactivo
async def ejecutar_grounding_interactivo(destinatario):
    """Inicia el ejercicio de grounding que requiere respuestas del usuario"""
    ejercicios = cargar_ejercicios()
    if not ejercicios or "grounding" not in ejercicios:
        return
    
    await enviar_mensaje_whatsapp(
        destinatario,
        "Perfecto 🌍\n\nVamos a hacer el ejercicio de grounding paso a paso.\n\nTe iré guiando con cada sentido.",
        0
    )
    
    await enviar_mensaje_whatsapp(
        destinatario,
        "👀 Paso 1: VISTA\n\nMira a tu alrededor y dime:\n¿Qué 5 cosas puedes ver?\n\nPueden ser objetos, colores, formas... Tómate tu tiempo.",
        3
    )
    
    actualizar_sesion(destinatario, estado="en_ejercicio", ejercicio="grounding", paso=1, esperando=True)

# Continuar grounding según el paso
async def continuar_grounding(destinatario, respuesta_usuario, paso):
    """Continúa el ejercicio de grounding según el paso actual"""
    
    respuestas_empaticas = [
        f"Muy bien 👍\n\n{respuesta_usuario}\n\nGracias por compartir.",
        f"Excelente observación 🎵\n\n{respuesta_usuario}",
        f"Perfecto 👃\n\n{respuesta_usuario}",
        f"Genial 😊\n\n{respuesta_usuario}"
    ]
    
    proximos_pasos = [
        (2, "✋ Paso 2: TACTO\n\nAhora identifica:\n¿Qué 4 cosas puedes tocar?\n\nPuede ser la textura de tu ropa, una superficie, el aire..."),
        (2, "👂 Paso 3: OÍDO\n\nConcentra tu atención:\n¿Qué 3 sonidos puedes escuchar?\n\nPueden ser cercanos o lejanos, fuertes o sutiles."),
        (2, "👃 Paso 4: OLFATO\n\nAhora nota:\n¿Qué 2 aromas puedes percibir?\n\nPuede ser el aire, tu perfume, cualquier olor sutil."),
        (2, "👅 Paso 5: GUSTO\n\nFinalmente:\n¿Qué 1 sabor percibes o recuerdas?\n\nPuede ser el sabor en tu boca o un sabor que te guste.")
    ]
    
    if paso <= len(respuestas_empaticas):
        # Responder empáticamente
        await enviar_mensaje_whatsapp(destinatario, respuestas_empaticas[paso - 1], 1)
        
        # Dar el siguiente paso
        if paso < len(proximos_pasos):
            delay, siguiente_instruccion = proximos_pasos[paso - 1]
            await enviar_mensaje_whatsapp(destinatario, siguiente_instruccion, delay)
            actualizar_sesion(destinatario, paso=paso + 1, esperando=True)
        else:
            # Finalizar
            await enviar_mensaje_whatsapp(
                destinatario,
                "🎉 ¡Lo lograste! 🎉\n\nHas completado el ejercicio de grounding.\n\n¿Te sientes más conectado con el presente?\n\nEscribe *menu* para volver al inicio.",
                2
            )
            actualizar_sesion(destinatario, estado="esperando_feedback", esperando=True)

# Ejecutar mindfulness automático
async def ejecutar_mindfulness_automatico(destinatario):
    """Ejecuta mindfulness con mensajes automáticos"""
    
    pasos_mindfulness = [
        (0, "🧘 Vamos a practicar un momento de mindfulness..."),
        (3, "Siéntate cómodamente.\n\nCierra los ojos si te sientes seguro haciéndolo.\n\nRespira naturalmente."),
        (8, "Observa tu respiración...\n\n¿Cómo entra el aire?\n¿Cómo sale?\n\nSolo observa, sin juzgar."),
        (10, "Ahora lleva tu atención a tu cuerpo.\n\n¿Sientes tensión en algún lugar?\n\nHombros... Mandíbula... Frente..."),
        (8, "No intentes cambiar nada.\n\nSolo observa con curiosidad y amabilidad hacia ti mismo."),
        (10, "Si tu mente divaga, está bien.\n\nEs completamente normal.\n\nSimplemente nota que estás pensando..."),
        (5, "Y con suavidad, vuelve tu atención a tu respiración."),
        (8, "✨ Muy bien hecho ✨\n\nCada vez que practicas, fortaleces tu capacidad de estar presente.\n\nEscribe *menu* cuando quieras volver al inicio.")
    ]
    
    for delay, mensaje in pasos_mindfulness:
        await enviar_mensaje_whatsapp(destinatario, mensaje, delay)
    
    actualizar_sesion(destinatario, estado="menu", esperando=False)

# Iniciar ejercicio
def iniciar_ejercicio(user_id, tipo_ejercicio, background_tasks: BackgroundTasks):
    ejercicios = cargar_ejercicios()
    if not ejercicios or tipo_ejercicio not in ejercicios:
        return "Lo siento, ese ejercicio no está disponible."
    
    if tipo_ejercicio == "respiracion":
        # Ejercicio automático
        background_tasks.add_task(ejecutar_respiracion_automatica, user_id)
        actualizar_sesion(user_id, estado="en_ejercicio_auto", ejercicio=tipo_ejercicio)
        return ejercicios[tipo_ejercicio]["introduccion"]
    
    elif tipo_ejercicio == "grounding":
        # Ejercicio interactivo
        background_tasks.add_task(ejecutar_grounding_interactivo, user_id)
        actualizar_sesion(user_id, estado="iniciando_ejercicio", ejercicio=tipo_ejercicio)
        return "Preparando el ejercicio de grounding... 🌍"
    
    elif tipo_ejercicio == "mindfulness":
        # Ejercicio automático
        background_tasks.add_task(ejecutar_mindfulness_automatico, user_id)
        actualizar_sesion(user_id, estado="en_ejercicio_auto", ejercicio=tipo_ejercicio)
        return ejercicios[tipo_ejercicio]["introduccion"]
    
    return "Ejercicio no implementado aún."

# Procesar mensaje del usuario
def procesar_mensaje(user_id, texto_usuario, background_tasks: BackgroundTasks):
    menu = cargar_menu()
    if not menu:
        return "Error del sistema. Por favor intenta más tarde."
    
    sesion = obtener_sesion(user_id)
    texto = texto_usuario.strip()
    
    # Comandos globales
    if texto.lower() in ["menu", "salir", "cancelar", "stop"]:
        reiniciar_sesion(user_id)
        return formatear_menu_whatsapp()
    
    # Si está esperando feedback después de un ejercicio
    if sesion["estado"] == "esperando_feedback":
        reiniciar_sesion(user_id)
        return f"Me alegra que hayas compartido eso. 💚\n\n{formatear_menu_whatsapp()}"
    
    # Si está en grounding interactivo
    if sesion["estado"] == "en_ejercicio" and sesion["ejercicio_actual"] == "grounding":
        if sesion["esperando_respuesta"]:
            paso = sesion["paso_actual"]
            background_tasks.add_task(continuar_grounding, user_id, texto, paso)
            actualizar_sesion(user_id, esperando=False)
            return None  # No responder inmediatamente, lo hará la tarea en background
    
    # Menú principal
    if texto.lower() in ["hola", "inicio", "start", "hi", "hello"]:
        reiniciar_sesion(user_id)
        return formatear_menu_whatsapp()
    
    # Ayuda urgente
    if texto.lower() in ["urgente", "ayuda", "sos", "emergency", "emergencia", "auxilio"]:
        return menu["ayuda_urgente"]["mensaje"]
    
    # Selección por número
    try:
        opcion_num = int(texto)
        opciones = menu["menu_principal"]["opciones"]
        
        for opcion in opciones:
            if opcion["id"] == opcion_num:
                categoria = opcion["categoria"]
                
                if categoria == "urgente":
                    return menu["ayuda_urgente"]["mensaje"]
                
                if categoria in ["respiracion", "grounding", "mindfulness"]:
                    return iniciar_ejercicio(user_id, categoria, background_tasks)
                
                # Técnicas pendientes
                respuesta = f"{opcion['emoji']} *{opcion['nombre']}*\n\n"
                respuesta += f"{opcion['descripcion']}\n\n"
                respuesta += "_Esta técnica estará disponible próximamente._\n\n"
                respuesta += "Escribe *menu* para volver al inicio."
                return respuesta
        
        return "❌ Opción no válida. Escribe *menu* para ver las opciones."
    
    except ValueError:
        return "No entendí tu mensaje. 🤔\n\nEscribe *menu* para ver las opciones."

# Endpoints
@app.get("/")
def root():
    return {
        "status": "✅ AIuda WhatsApp Bot funcionando",
        "version": "2.1.0 - Ejercicios Automáticos",
        "webhook": "/whatsapp",
        "ejercicios_automaticos": ["respiracion", "mindfulness"],
        "ejercicios_interactivos": ["grounding"],
        "twilio_configurado": twilio_client is not None
    }

@app.post("/whatsapp")
async def whatsapp_webhook(
    background_tasks: BackgroundTasks,
    Body: str = Form(...),
    From: str = Form(...),
    ProfileName: str = Form(None)
):
    """Recibe mensajes de WhatsApp vía Twilio y responde"""
    
    try:
        print(f"\n{'='*60}")
        print(f"📩 Mensaje recibido")
        print(f"   De: {ProfileName} ({From})")
        print(f"   Texto: {Body}")
        
        sesion = obtener_sesion(From)
        print(f"   Estado: {sesion['estado']}")
        if sesion['ejercicio_actual']:
            print(f"   Ejercicio: {sesion['ejercicio_actual']} - Paso: {sesion['paso_actual']}")
        print(f"{'='*60}")
        
        # Procesar mensaje
        respuesta_texto = procesar_mensaje(From, Body, background_tasks)
        
        # Si no hay respuesta inmediata (ej: grounding procesándose)
        if respuesta_texto is None:
            resp = MessagingResponse()
            return Response(content=str(resp), media_type="application/xml")
        
        print(f"📤 Respuesta: {respuesta_texto[:100]}...")
        print(f"{'='*60}\n")
        
        resp = MessagingResponse()
        resp.message(respuesta_texto)
        
        return Response(content=str(resp), media_type="application/xml")
    
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ ERROR: {e}")
        print(f"{'='*60}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        resp = MessagingResponse()
        resp.message("Error técnico. Escribe *menu* para reintentar.")
        return Response(content=str(resp), media_type="application/xml")

@app.get("/test")
def test_bot():
    return {
        "menu": formatear_menu_whatsapp(),
        "sesiones_activas": len(sesiones_usuario),
        "twilio_configurado": twilio_client is not None
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 AIuda WhatsApp Bot v2.1 - Ejercicios Automáticos")
    print("="*60)
    print("📍 Servidor: http://0.0.0.0:5000")
    print("✨ Funcionalidades:")
    print("   🫁 Respiración: Automática con pausas reales")
    print("   🌍 Grounding: Interactiva con respuestas empáticas")
    print("   🧘 Mindfulness: Automática guiada")
    print("="*60)
    
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("\n⚠️  ADVERTENCIA: Credenciales de Twilio no configuradas")
        print("   Los ejercicios automáticos no funcionarán correctamente")
        print("   Configura las variables de entorno:")
        print("   - TWILIO_ACCOUNT_SID")
        print("   - TWILIO_AUTH_TOKEN")
        print("   - TWILIO_WHATSAPP_NUMBER")
        print("="*60)
    
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000)