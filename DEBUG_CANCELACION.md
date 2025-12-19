# 🐛 Debug: Problema con Cancelación de Reservas WhatsApp

## Problema Reportado
El usuario creó una reserva desde WhatsApp pero al intentar cancelarla, el sistema no encuentra la reserva.

## Conversación de Prueba
```
Usuario: "quiero hacer una reserva para hoy en la cancha A"
Bot: Lista horarios disponibles
Usuario: "reserva de 10 a 11"
Bot: Confirma disponibilidad
Usuario: "si"
Bot: ✅ Reserva confirmada + datos de pago
Usuario: "si ahora quiero cancelar la reserva que hice para hoy a las 10"
Bot: ❌ "No encuentro ninguna reserva a tu nombre para hoy a las 10:00"
```

## Hipótesis del Problema
El número de teléfono que viene de WhatsApp (`from_number`) puede estar en un formato diferente entre:
1. Cuando se CREA la reserva (función `crear_reserva`)
2. Cuando se LISTA/CANCELA la reserva (función `listar_reservas_usuario`)

### Posibles causas:
- El número puede venir con prefijo diferente (ej: `549...` vs `54...`)
- El número puede tener formato diferente en diferentes mensajes
- El cliente se está creando con un número pero se está buscando con otro

## Cambios Realizados (Debug)

### 1. `/home/mateo/dev/padelpro/back/wsp.py`
Agregados logs para rastrear el `from_number`:
```python
print(f"DEBUG WSP: Mensaje recibido de número: {from_number}")
print(f"DEBUG WSP: crear_reserva_wrapper llamado con telefono={from_number}")
print(f"DEBUG WSP: Llamando chat_with_assistant con usuario={from_number}")
```

### 2. `/home/mateo/dev/padelpro/back/abml_reservas.py`

#### En `crear_reserva()`:
```python
print(f"DEBUG crear_reserva: Buscando cliente con telefono={telefono}")
print(f"DEBUG crear_reserva: Cliente encontrado: ID={cliente.id}, nombre={cliente.nombre}, telefono={cliente.telefono}")
print(f"DEBUG crear_reserva: Creando nuevo cliente con telefono={telefono}, nombre={nombre_cliente}")
print(f"DEBUG crear_reserva: Cliente creado con ID={cliente.id}")
```

#### En `listar_reservas_usuario()`:
```python
print(f"DEBUG: listar_reservas_usuario llamado con telefono={telefono}")
print(f"DEBUG: Cliente encontrado: {cliente}")
print(f"DEBUG: No se encontró cliente con telefono={telefono}")
print(f"DEBUG: Cliente ID={cliente.id}, nombre={cliente.nombre}, telefono={cliente.telefono}")
print(f"DEBUG: Reservas encontradas: {len(reservas)}")
print(f"DEBUG: Reservas formateadas: {reservas_info}")
print(f"DEBUG ERROR: {str(e)}")
```

## Pasos para Diagnosticar

### 1. Reiniciar el servidor Flask
```bash
# Detener el servidor actual
# Reiniciar con:
python back/app.py
```

### 2. Hacer una prueba desde WhatsApp
Enviar los siguientes mensajes:
```
1. "quiero hacer una reserva para hoy en la cancha A"
2. "reserva de 10 a 11"
3. "si"
4. "quiero cancelar mi reserva"
```

### 3. Revisar los logs del servidor
Buscar en la consola del servidor los mensajes que empiezan con `DEBUG`:

**Al crear la reserva:**
```
DEBUG WSP: Mensaje recibido de número: 5491112345678
DEBUG WSP: crear_reserva_wrapper llamado con telefono=5491112345678
DEBUG crear_reserva: Buscando cliente con telefono=5491112345678
DEBUG crear_reserva: Creando nuevo cliente con telefono=5491112345678, nombre=5491112345678
DEBUG crear_reserva: Cliente creado con ID=123
```

**Al listar reservas:**
```
DEBUG WSP: Mensaje recibido de número: 5491112345678  <-- ¿Es el mismo?
DEBUG: listar_reservas_usuario llamado con telefono=5491112345678  <-- ¿Es el mismo?
DEBUG: Cliente encontrado: <Cliente ...>
DEBUG: Cliente ID=123, nombre=5491112345678, telefono=5491112345678
DEBUG: Reservas encontradas: 1
```

### 4. Comparar los números
**IMPORTANTE:** Verificar que el `from_number` sea EXACTAMENTE el mismo en:
- La creación de la reserva
- La búsqueda de reservas

## Posibles Soluciones

### Si el problema es formato de número:

#### Opción A: Normalizar el número antes de guardar/buscar
```python
def normalizar_telefono(telefono: str) -> str:
    """Normaliza el número de teléfono eliminando espacios, guiones, etc."""
    if not telefono:
        return telefono
    # Eliminar espacios, guiones, paréntesis
    telefono = telefono.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    # Si empieza con +, quitarlo
    if telefono.startswith('+'):
        telefono = telefono[1:]
    return telefono
```

#### Opción B: Búsqueda flexible por LIKE
```python
# En lugar de:
cliente = Cliente.query.filter_by(telefono=str(telefono)).first()

# Usar:
cliente = Cliente.query.filter(
    Cliente.telefono.like(f'%{telefono[-10:]}%')  # Últimos 10 dígitos
).first()
```

### Si el problema es que el cliente no se está creando:
Verificar que el wrapper esté pasando correctamente el `telefono`:
```python
def crear_reserva_wrapper(**kwargs):
    print(f"DEBUG: kwargs antes de agregar telefono: {kwargs}")
    kwargs['telefono'] = from_number
    print(f"DEBUG: kwargs después de agregar telefono: {kwargs}")
    return crear_reserva(**kwargs)
```

## Verificación en Base de Datos

### Consultar clientes creados:
```sql
SELECT id, nombre, apellido, telefono FROM cliente ORDER BY id DESC LIMIT 10;
```

### Consultar reservas recientes:
```sql
SELECT r.id, r.fecha, r.hora, c.nombre as cancha, cl.telefono, e.nombre as estado
FROM reserva r
JOIN cancha c ON r.cancha_id = c.id
JOIN cliente cl ON r.cliente_id = cl.id
JOIN estado e ON r.estado_id = e.id
ORDER BY r.id DESC LIMIT 10;
```

### Verificar si hay duplicados de clientes:
```sql
SELECT telefono, COUNT(*) as cantidad
FROM cliente
GROUP BY telefono
HAVING cantidad > 1;
```

## Próximos Pasos

1. ✅ Reiniciar servidor con logs de debug
2. ⏳ Hacer prueba desde WhatsApp
3. ⏳ Revisar logs en consola
4. ⏳ Identificar la discrepancia exacta
5. ⏳ Aplicar la solución correspondiente
6. ⏳ Remover logs de debug una vez resuelto

## Notas
- Los logs se agregaron en puntos estratégicos para rastrear el flujo completo
- Una vez identificado el problema, se debe aplicar la solución y remover los `print()` de debug
- Es importante verificar que el número de teléfono sea consistente en TODA la aplicación
