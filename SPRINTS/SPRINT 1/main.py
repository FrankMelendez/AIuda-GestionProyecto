from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import uvicorn

app = FastAPI(title="AIuda API", version="1.0.0")

# Modelos de datos
class SeleccionUsuario(BaseModel):
    opcion: int

# Cargar configuración
def cargar_menu():
    with open("menu.json", "r", encoding="utf-8") as f:
        return json.load(f)

# Formatear menú principal
def formatear_menu_principal(menu_data):
    mensaje = menu_data["bienvenida"] + "\n\n"
    mensaje += menu_data["menu_principal"]["titulo"] + "\n\n"
    
    for opcion in menu_data["menu_principal"]["opciones"]:
        mensaje += f"{opcion['emoji']} {opcion['id']}. {opcion['nombre']}\n"
        mensaje += f"   {opcion['descripcion']}\n\n"
    
    mensaje += "Escribe el número de la opción que prefieras."
    return mensaje

# Endpoints
@app.get("/")
def root():
    return {
        "status": "✅ AIuda API funcionando",
        "version": "1.0.0",
        "endpoints": {
            "menu": "/menu",
            "seleccionar": "/seleccionar (POST)",
            "ayuda_urgente": "/urgente"
        }
    }

@app.get("/menu")
def mostrar_menu():
    """Muestra el menú principal con todas las opciones"""
    menu = cargar_menu()
    mensaje = formatear_menu_principal(menu)
    
    return {
        "message": mensaje,
        "opciones": menu["menu_principal"]["opciones"]
    }

@app.post("/seleccionar")
def seleccionar_opcion(seleccion: SeleccionUsuario):
    """Procesa la selección del usuario"""
    menu = cargar_menu()
    
    # Buscar opción
    opcion_elegida = None
    for opcion in menu["menu_principal"]["opciones"]:
        if opcion["id"] == seleccion.opcion:
            opcion_elegida = opcion
            break
    
    if not opcion_elegida:
        raise HTTPException(
            status_code=400, 
            detail="Opción inválida. Por favor elige un número del 1 al 6."
        )
    
    # Caso especial: Ayuda urgente
    if opcion_elegida["categoria"] == "urgente":
        return {
            "tipo": "urgente",
            "message": menu["ayuda_urgente"]["mensaje"],
            "recursos": menu["ayuda_urgente"]["recursos"]
        }
    
    # Respuesta para otras categorías
    return {
        "tipo": opcion_elegida["categoria"],
        "message": f"✅ Has elegido: {opcion_elegida['nombre']}\n\n{opcion_elegida['descripcion']}",
        "tecnica": opcion_elegida,
        "siguiente_paso": f"Preparando {opcion_elegida['nombre'].lower()}..."
    }

@app.get("/urgente")
def ayuda_urgente():
    """Muestra recursos de ayuda inmediata"""
    menu = cargar_menu()
    return {
        "message": menu["ayuda_urgente"]["mensaje"],
        "recursos": menu["ayuda_urgente"]["recursos"]
    }

@app.get("/categoria/{nombre}")
def obtener_por_categoria(nombre: str):
    """Obtiene opciones por categoría"""
    menu = cargar_menu()
    opciones = [
        op for op in menu["menu_principal"]["opciones"] 
        if op["categoria"] == nombre
    ]
    
    if not opciones:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    return {"categoria": nombre, "opciones": opciones}

if __name__ == "__main__":
    uvicorn.run(app, host="192.168.56.1", port=1234)