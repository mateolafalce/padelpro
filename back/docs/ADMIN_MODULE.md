# Módulo de Administración - PadelPro

## Descripción

El módulo de administración permite configurar todos los datos del sistema:
- **Información del negocio**: Nombre, tipo y ubicación
- **Datos de pago**: CBU y Alias para transferencias

Estos valores se utilizan en el chatbot de IA para personalizar las respuestas y proporcionar información de pago a los clientes después de confirmar una reserva.

## Características

### Frontend (`/admin`)
- **Interfaz moderna y responsive** con diseño premium
- **Visualización de valores actuales** de CBU y Alias
- **Formulario de edición** con validación en tiempo real
- **Feedback visual** con alertas de éxito/error
- **Animaciones suaves** para mejor experiencia de usuario

### Backend

#### Endpoints API

1. **GET `/api/configuracion`**
   - Obtiene la configuración actual de CBU y Alias
   - Respuesta:
     ```json
     {
       "success": true,
       "cbu": "1234567890123456789012",
       "alias": "padelpro.pagos"
     }
     ```

2. **POST `/api/configuracion`**
   - Actualiza la configuración de CBU y Alias
   - Body:
     ```json
     {
       "cbu": "1234567890123456789012",
       "alias": "padelpro.pagos"
     }
     ```
   - Respuesta:
     ```json
     {
       "success": true,
       "message": "Configuración actualizada correctamente"
     }
     ```

### Base de Datos

Nueva tabla `configuracion`:
- `id` (INT, PRIMARY KEY, AUTO_INCREMENT)
- `clave` (VARCHAR(50), UNIQUE, NOT NULL)
- `valor` (VARCHAR(255))

Registros iniciales:
- `clave='cbu'`, `valor=''`
- `clave='alias'`, `valor=''`

## Integración con el Chatbot

El chatbot de IA (`ai.py`) ahora obtiene dinámicamente los valores de CBU y Alias desde la base de datos en lugar de las variables de entorno. Esto permite que los cambios realizados desde el módulo de administración se reflejen inmediatamente en las respuestas del chatbot.

Cuando un cliente confirma una reserva, el chatbot automáticamente incluye:
- El monto a pagar
- El CBU configurado
- El Alias configurado

## Validaciones

### CBU
- Debe contener exactamente 22 dígitos
- Solo acepta caracteres numéricos

### Alias
- Máximo 50 caracteres
- Acepta letras, números y caracteres especiales comunes

## Uso

1. Acceder al módulo desde el menú principal haciendo clic en "⚙️ Administración"
2. Los valores actuales se cargan automáticamente
3. Modificar los campos según sea necesario
4. Hacer clic en "💾 Guardar Configuración"
5. Los cambios se aplican inmediatamente tanto en la BD como en el archivo `.env`

## Archivos Relacionados

- **Backend:**
  - `/back/admin_config.py` - Blueprint con endpoints de administración
  - `/back/bd.py` - Modelo de datos `Configuracion`
  - `/back/ai.py` - Integración con chatbot
  - `/back/main.py` - Registro del blueprint

- **Frontend:**
  - `/front/admin.html` - Interfaz de administración
  - `/front/index.html` - Menú principal (incluye tarjeta de admin)

- **Migración:**
  - `/back/add_config_table.py` - Script de migración para crear la tabla

## Notas Técnicas

- Los valores se almacenan tanto en la BD como en el archivo `.env` para mantener compatibilidad
- Si hay error al consultar la BD, el sistema usa los valores del `.env` como fallback
- La actualización es atómica: si falla la BD, se hace rollback automático
