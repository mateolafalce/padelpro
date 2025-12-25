# Configuración de WhatsApp Business API para PadelPro

## 📋 Requisitos previos

1. Cuenta de Meta for Developers (https://developers.facebook.com/)
2. Aplicación de WhatsApp Business creada
3. Número de teléfono verificado en WhatsApp Business

## 🔧 Configuración paso a paso

### 1. Crear aplicación en Meta for Developers

1. Ve a https://developers.facebook.com/
2. Crea una nueva aplicación
3. Selecciona "Business" como tipo de aplicación
4. Agrega el producto "WhatsApp"

### 2. Obtener credenciales

Desde el panel de WhatsApp Business API, obtén:

- **WHATSAPP_TOKEN**: Token de acceso permanente
  - Ve a "API Setup" → "Temporary access token" (temporal)
  - Para producción, genera un token permanente desde "System Users"
  
- **WHATSAPP_PHONE_NUMBER_ID**: ID del número de teléfono
  - Visible en "API Setup" → "Phone number ID"

- **WHATSAPP_VERIFY_TOKEN**: Token personalizado para verificar el webhook
  - Puedes usar cualquier string (ej: `padelpro_verify_token_2024`)

### 3. Configurar variables de entorno

Copia `.env.example` a `.env` y completa:

```bash
WHATSAPP_TOKEN=EAAxxxxxxxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_VERIFY_TOKEN=padelpro_verify_token_2024
```

### 4. Configurar webhook en Meta

1. En el panel de WhatsApp → "Configuration" → "Webhook"
2. Haz clic en "Edit"
3. Ingresa tu URL de callback:
   ```
   https://padelpro.duckdns.org/api/whatsapp/webhook
   ```
4. Ingresa el **Verify Token** (debe coincidir con `WHATSAPP_VERIFY_TOKEN`)
5. Suscríbete a los eventos:
   - ✅ `messages`

### 5. Exponer tu servidor local (para desarrollo)

Usa ngrok para exponer tu servidor local:

```bash
ngrok http 8080
```

Copia la URL HTTPS que te da ngrok y úsala como webhook URL.

## 🧪 Testing

### Verificar webhook (GET)
```bash
curl "http://localhost:8080/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=padelpro_verify_token_2024&hub.challenge=test123"
```

Debería devolver: `test123`

### Enviar mensaje manual (POST)
```bash
<curl -X POST http://localhost:8080/api/whatsapp/send \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "5491112345678",
    "message": "Hola desde PadelPro!"
  }'>
```

### Limpiar historial de conversación
```bash
curl -X DELETE http://localhost:8080/api/whatsapp/clear-history/5491112345678
```

## 📱 Uso

Una vez configurado:

1. Los usuarios envían mensajes a tu número de WhatsApp Business
2. El webhook recibe el mensaje
3. El chatbot AI procesa la solicitud
4. La respuesta se envía automáticamente al usuario

## 🔐 Seguridad

- **Producción**: Usa tokens permanentes, no temporales
- **HTTPS**: WhatsApp requiere HTTPS para webhooks
- **Validación**: El webhook valida el token de verificación
- **Rate limiting**: Considera agregar rate limiting para evitar spam

## 📊 Endpoints disponibles

- `GET /api/whatsapp/webhook` - Verificación del webhook
- `POST /api/whatsapp/webhook` - Recepción de mensajes
- `POST /api/whatsapp/send` - Envío manual de mensajes
- `DELETE /api/whatsapp/clear-history/<phone>` - Limpiar historial

## 🚀 Producción

Para producción, considera:

1. **Almacenamiento persistente**: Usa Redis o base de datos para `conversation_store`
2. **Logging**: Implementa logging robusto
3. **Monitoreo**: Monitorea el estado del webhook
4. **Escalabilidad**: Usa workers asíncronos (Celery, RQ)
5. **Backup**: Guarda conversaciones importantes

## 🐛 Troubleshooting

**Webhook no se verifica:**
- Verifica que el `WHATSAPP_VERIFY_TOKEN` coincida
- Asegúrate de que la URL sea accesible públicamente (HTTPS)

**No recibo mensajes:**
- Verifica que estés suscrito al evento `messages`
- Revisa los logs del servidor
- Verifica que el token de acceso sea válido

**Errores al enviar mensajes:**
- Verifica que `WHATSAPP_TOKEN` y `WHATSAPP_PHONE_NUMBER_ID` sean correctos
- Asegúrate de que el número de destino esté en formato internacional (+5491112345678)
