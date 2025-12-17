# Sistema de Historial de Conversaciones - PadelPro

## Descripción

Sistema completo de gestión de historial de conversaciones que almacena todos los mensajes intercambiados entre usuarios y el asistente de IA en la base de datos. Soporta tanto conversaciones locales (chat web) como de WhatsApp.

## Características

### 🗄️ **Base de Datos**

**Tabla: `conversacion`**
- `id` (INT, PRIMARY KEY, AUTO_INCREMENT)
- `fecha` (DATETIME, DEFAULT CURRENT_TIMESTAMP)
- `usuario` (VARCHAR(50), NOT NULL) - Número de teléfono o '99999999' para local
- `rol` (VARCHAR(20), NOT NULL) - 'user' o 'assistant'
- `mensaje` (TEXT, NOT NULL)

### 📝 **Identificación de Usuarios**

- **Chat Local**: Usuario `99999999`
- **WhatsApp**: Número de teléfono completo (ej: `5491112345678`)

### 🔄 **Flujo de Funcionamiento**

1. **Usuario envía mensaje** → Se guarda en BD con rol='user'
2. **Sistema obtiene últimos 10 mensajes** desde BD
3. **IA genera respuesta** usando el contexto del historial
4. **Respuesta se guarda** en BD con rol='assistant'
5. **Se limpia historial antiguo** (mantiene últimos 50 mensajes)

## API Endpoints

### Chat Local (`/api/chat/message`)

**POST** - Enviar mensaje en chat local
```json
{
  "message": "Hola, quiero reservar una cancha"
}
```

**Respuesta:**
```json
{
  "success": true,
  "response": "¡Hola! Con gusto te ayudo..."
}
```

### WhatsApp (`/api/whatsapp/webhook`)

**POST** - Webhook para recibir mensajes de WhatsApp
- Automáticamente guarda y recupera historial por número de teléfono
- Mantiene contexto de conversación

**DELETE** `/api/whatsapp/clear-history/<phone_number>`
- Elimina todo el historial de un número

### Gestión de Historial (`/api/historial/*`)

#### 1. **Listar Usuarios**
**GET** `/api/historial/usuarios?page=1&per_page=10`

Respuesta:
```json
{
  "success": true,
  "usuarios": [
    {
      "usuario": "5491112345678",
      "total_mensajes": 24,
      "ultimo_mensaje": "2025-12-17T20:30:00",
      "tipo": "WhatsApp"
    },
    {
      "usuario": "99999999",
      "total_mensajes": 16,
      "ultimo_mensaje": "2025-12-17T19:45:00",
      "tipo": "Local"
    }
  ],
  "page": 1,
  "per_page": 10,
  "total": 2,
  "pages": 1
}
```

#### 2. **Ver Conversación de Usuario**
**GET** `/api/historial/usuario/<usuario>?limite=50`

Respuesta:
```json
{
  "success": true,
  "usuario": "99999999",
  "mensajes": [
    {
      "role": "user",
      "content": "Hola"
    },
    {
      "role": "assistant",
      "content": "¡Hola! ¿En qué puedo ayudarte?"
    }
  ],
  "estadisticas": {
    "total_mensajes": 16,
    "mensajes_usuario": 8,
    "mensajes_asistente": 8,
    "primer_mensaje": "2025-12-17T18:00:00",
    "ultimo_mensaje": "2025-12-17T19:45:00"
  }
}
```

#### 3. **Eliminar Historial de Usuario**
**DELETE** `/api/historial/usuario/<usuario>`

Respuesta:
```json
{
  "success": true,
  "message": "Historial de 99999999 eliminado correctamente"
}
```

#### 4. **Estadísticas Generales**
**GET** `/api/historial/estadisticas`

Respuesta:
```json
{
  "success": true,
  "estadisticas": {
    "total_mensajes": 150,
    "total_usuarios": 12,
    "usuarios_activos_hoy": 5,
    "mensajes_por_rol": {
      "user": 75,
      "assistant": 75
    }
  }
}
```

## Funciones Utilitarias (`historial_utils.py`)

### `guardar_mensaje(usuario, rol, mensaje)`
Guarda un mensaje en el historial.

```python
from historial_utils import guardar_mensaje

guardar_mensaje('99999999', 'user', 'Hola')
guardar_mensaje('99999999', 'assistant', '¡Hola! ¿En qué puedo ayudarte?')
```

### `obtener_historial(usuario, limite=10)`
Obtiene los últimos N mensajes de un usuario.

```python
from historial_utils import obtener_historial

mensajes = obtener_historial('99999999', limite=10)
# Retorna: [{'role': 'user', 'content': '...'}, ...]
```

### `limpiar_historial_antiguo(usuario, mantener_ultimos=50)`
Limpia mensajes antiguos manteniendo solo los últimos N.

```python
from historial_utils import limpiar_historial_antiguo

limpiar_historial_antiguo('99999999', mantener_ultimos=50)
```

### `obtener_estadisticas_usuario(usuario)`
Obtiene estadísticas de conversación de un usuario.

```python
from historial_utils import obtener_estadisticas_usuario

stats = obtener_estadisticas_usuario('99999999')
```

## Integración

### Chat Local (`chat_bp.py`)
- ✅ Guarda automáticamente cada mensaje
- ✅ Obtiene historial desde BD (no desde frontend)
- ✅ Limpia historial antiguo

### WhatsApp (`wsp.py`)
- ✅ Guarda mensajes por número de teléfono
- ✅ Mantiene contexto entre conversaciones
- ✅ Elimina `conversation_store` en memoria

### Frontend (`chat.html`)
- ✅ Ya NO envía historial al backend
- ✅ Solo envía el mensaje actual
- ✅ Más ligero y eficiente

## Ventajas del Sistema

1. **Persistencia**: Los mensajes se guardan permanentemente
2. **Contexto**: El asistente recuerda conversaciones anteriores
3. **Escalabilidad**: No depende de memoria del servidor
4. **Análisis**: Permite obtener estadísticas y métricas
5. **Multi-canal**: Soporta chat local y WhatsApp
6. **Gestión**: Endpoints para administrar conversaciones

## Configuración

### Límites por Defecto
- **Contexto enviado a IA**: 10 últimos mensajes
- **Mensajes mantenidos por usuario**: 50
- **Paginación de usuarios**: 10 por página

Estos valores pueden ajustarse según necesidad.

## Archivos Relacionados

**Backend:**
- `/back/bd.py` - Modelo `Conversacion`
- `/back/historial_utils.py` - Funciones utilitarias
- `/back/historial_bp.py` - Blueprint de gestión
- `/back/chat_bp.py` - Chat local (actualizado)
- `/back/wsp.py` - WhatsApp (actualizado)
- `/back/main.py` - Registro del blueprint

**Frontend:**
- `/front/chat.html` - Interfaz de chat (simplificada)

**Migración:**
- `/back/add_conversacion_table.py` - Script de migración (ejecutado ✅)

## Ejemplos de Uso

### Obtener historial de un usuario
```bash
curl http://localhost:8080/api/historial/usuario/99999999
```

### Listar todos los usuarios con conversaciones
```bash
curl http://localhost:8080/api/historial/usuarios
```

### Ver estadísticas generales
```bash
curl http://localhost:8080/api/historial/estadisticas
```

### Eliminar historial de un usuario
```bash
curl -X DELETE http://localhost:8080/api/historial/usuario/99999999
```

## Notas Importantes

- Los mensajes se guardan automáticamente, no requiere acción manual
- El sistema limpia automáticamente mensajes antiguos
- El historial es específico por usuario (número de teléfono o ID local)
- Los mensajes incluyen timestamp automático
- Compatible con el sistema existente de reservas y verificación

```bash
# Listar usuarios con conversaciones
curl http://localhost:8080/api/historial/usuarios

# Ver conversación de usuario local
curl http://localhost:8080/api/historial/usuario/99999999

# Estadísticas generales
curl http://localhost:8080/api/historial/estadisticas

# Eliminar historial de un usuario
curl -X DELETE http://localhost:8080/api/historial/usuario/99999999
```