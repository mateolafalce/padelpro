# 🚫 Sistema de Cancelación de Reservas

## Resumen
Los usuarios pueden cancelar sus propias reservas que están en estado "iniciada" (no ejecutadas) a través del chatbot, tanto desde la interfaz web local como desde WhatsApp.

## Flujo de Cancelación

### 1. Usuario solicita cancelar
El usuario puede decir cosas como:
- "Quiero cancelar mi reserva"
- "Cancelar reserva"
- "Necesito cancelar"
- "Borrar mi reserva"

### 2. El sistema lista automáticamente las reservas
- El chatbot llama automáticamente a `listar_reservas_usuario()` usando el teléfono del usuario
- **NO** se le pide al usuario su número de teléfono (el sistema ya lo tiene)
- Se muestran solo las reservas en estado "iniciada"

### 3. Presentación de reservas
El chatbot presenta las reservas de forma clara:
```
Tenés las siguientes reservas pendientes:

1. Cancha A - 25/12/2025 a las 18:00-19:00 ($2500)
2. Cancha B - 26/12/2025 a las 20:00-21:00 ($3000)

¿Cuál querés cancelar?
```

### 4. Usuario selecciona la reserva
El usuario puede responder:
- Por número: "La 1" o "La primera"
- Por cancha: "La de Cancha A"
- Por fecha: "La del 25"

### 5. Cancelación
- El chatbot identifica el ID de la reserva
- Llama a `cancelar_reserva_usuario(reserva_id, telefono)`
- Cambia el estado de "iniciada" a "cancelada"
- Confirma al usuario que la cancelación fue exitosa

### 6. Confirmación
```
✅ Reserva cancelada exitosamente. Cancha A del 25/12/2025 a las 18:00-19:00.
El horario ahora está disponible para otros usuarios.
```

## Funciones Implementadas

### `listar_reservas_usuario(telefono: str)`
**Ubicación:** `back/abml_reservas.py` (líneas 138-190)

**Qué hace:**
- Busca el cliente por número de teléfono
- Obtiene todas sus reservas en estado "iniciada"
- Las ordena por fecha y hora
- Retorna lista formateada con ID, cancha, fecha, hora, monto

**Retorno exitoso:**
```python
{
    'exito': True,
    'reservas': [
        {
            'id': 123,
            'cancha': 'Cancha A',
            'fecha': '25/12/2025',
            'hora': '18:00-19:00',
            'monto': 2500,
            'estado': 'iniciada'
        }
    ],
    'mensaje': 'Encontramos 1 reserva(s) pendiente(s)'
}
```

### `cancelar_reserva_usuario(reserva_id: int, telefono: str)`
**Ubicación:** `back/abml_reservas.py` (líneas 193-230)

**Qué hace:**
- Busca la reserva por ID
- Verifica que pertenezca al usuario (compara teléfono)
- Verifica que no esté ya cancelada
- Cambia el estado a "cancelada"
- Retorna confirmación

**Validaciones:**
- ✅ La reserva existe
- ✅ La reserva pertenece al usuario
- ✅ La reserva no está ya cancelada
- ✅ El estado "cancelada" existe en la BD

**Retorno exitoso:**
```python
{
    'exito': True,
    'mensaje': 'Reserva cancelada exitosamente. Cancha A del 25/12/2025 a las 18:00-19:00'
}
```

## Integración con IA

### Definiciones de funciones (ai.py)
El asistente de IA tiene acceso a dos funciones:

1. **`listar_reservas_usuario`** (líneas 227-239)
   - Parámetro: `telefono` (string)
   - El sistema inyecta automáticamente el teléfono del usuario

2. **`cancelar_reserva_usuario`** (líneas 241-257)
   - Parámetros: `reserva_id` (int), `telefono` (string)
   - El sistema inyecta automáticamente el teléfono del usuario

### Inyección automática del teléfono
En `ai.py` (líneas 358-367):
```python
elif function_name == "listar_reservas_usuario" and listar_reservas_func:
    if 'telefono' not in function_args and usuario:
        function_args['telefono'] = usuario
    function_response = listar_reservas_func(**function_args)
elif function_name == "cancelar_reserva_usuario" and cancelar_reserva_func:
    if 'telefono' not in function_args and usuario:
        function_args['telefono'] = usuario
    function_response = cancelar_reserva_func(**function_args)
```

## Canales Soportados

### 💬 Chat Local (front/chat.html)
- Usuario: `'99999999'` (usuario local por defecto)
- Endpoint: `/api/chat/message`
- Archivo: `back/chat_bp.py`

### 📱 WhatsApp
- Usuario: Número de teléfono del remitente (ej: `'5491112345678'`)
- Endpoint: `/api/whatsapp/webhook`
- Archivo: `back/wsp.py`

## Base de Datos

### Tabla: `estado`
Estados disponibles:
- `iniciada` - Reserva creada pero no ejecutada (puede cancelarse)
- `ejecutada` - Reserva ya realizada (NO puede cancelarse)
- `cancelada` - Reserva cancelada por el usuario
- `bloqueada` - Reserva bloqueada por admin

### Tabla: `reserva`
Campos relevantes:
- `id` - ID único de la reserva
- `cliente_id` - FK al cliente que hizo la reserva
- `estado_id` - FK al estado actual
- `fecha` - Fecha de la reserva
- `hora` - Horario (formato: "HH:MM-HH:MM")
- `monto` - Precio de la reserva

### Tabla: `cliente`
Campos relevantes:
- `id` - ID único del cliente
- `telefono` - Número de teléfono (usado para identificar al usuario)
- `nombre` - Nombre del cliente
- `apellido` - Apellido del cliente

## Ejemplos de Uso

### Ejemplo 1: Usuario con una reserva
```
Usuario: "Quiero cancelar mi reserva"

Bot: "Tenés 1 reserva pendiente:
     1. Cancha A - 25/12/2025 a las 18:00-19:00 ($2500)
     
     ¿Querés cancelar esta reserva?"

Usuario: "Sí"

Bot: "✅ Reserva cancelada exitosamente. Cancha A del 25/12/2025 a las 18:00-19:00.
     El horario ahora está disponible para otros usuarios."
```

### Ejemplo 2: Usuario con múltiples reservas
```
Usuario: "Cancelar reserva"

Bot: "Tenés las siguientes reservas pendientes:
     1. Cancha A - 25/12/2025 a las 18:00-19:00 ($2500)
     2. Cancha B - 26/12/2025 a las 20:00-21:00 ($3000)
     
     ¿Cuál querés cancelar?"

Usuario: "La del 26"

Bot: "✅ Reserva cancelada exitosamente. Cancha B del 26/12/2025 a las 20:00-21:00.
     El horario ahora está disponible para otros usuarios."
```

### Ejemplo 3: Usuario sin reservas
```
Usuario: "Quiero cancelar"

Bot: "No tenés reservas pendientes en este momento."
```

## Notas Importantes

1. ✅ **Solo se pueden cancelar reservas en estado "iniciada"**
   - Las reservas ejecutadas NO se pueden cancelar
   - Las reservas ya canceladas NO se pueden volver a cancelar

2. ✅ **Verificación de propiedad**
   - El sistema verifica que la reserva pertenezca al usuario
   - Se compara el teléfono del cliente con el del usuario actual

3. ✅ **Historial de conversación**
   - Todos los mensajes se guardan en la tabla `conversacion`
   - Se mantienen los últimos 50 mensajes por usuario

4. ✅ **Disponibilidad automática**
   - Al cancelar una reserva, el horario queda automáticamente disponible
   - Otros usuarios pueden reservar ese horario inmediatamente

## Testing

Para probar la funcionalidad:

1. **Crear una reserva de prueba** (como usuario local o WhatsApp)
2. **Solicitar cancelación**: "Quiero cancelar mi reserva"
3. **Verificar que se listen las reservas**
4. **Seleccionar la reserva a cancelar**
5. **Confirmar la cancelación**
6. **Verificar en la BD** que el estado cambió a "cancelada"

## Mejoras Futuras Sugeridas

- [ ] Permitir cancelación con tiempo límite (ej: solo hasta 2 horas antes)
- [ ] Enviar notificación por email al cancelar
- [ ] Permitir reprogramar en lugar de solo cancelar
- [ ] Estadísticas de cancelaciones por usuario
- [ ] Penalización por cancelaciones frecuentes
