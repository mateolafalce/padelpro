# Guía de Despliegue Rápido con Nginx y DuckDNS

Esta guía te ayudará a exponer tu aplicación **PadelPro** a internet utilizando tu dominio `padelpro.duckdns.org`.

## 1. Instalar Nginx

Primero, necesitas instalar el servidor web Nginx en tu máquina Linux.

```bash
sudo apt update
sudo apt install nginx -y
```

## 2. Configurar Nginx como Proxy Inverso

Vamos a configurar Nginx para que redirija el tráfico que llega a tu dominio hacia tu aplicación Flask que corre en el puerto 8080.

1.  Crea un nuevo archivo de configuración para tu sitio:

    ```bash
    sudo nano /etc/nginx/sites-available/padelpro
    ```

2.  Pega el siguiente contenido en ese archivo:

    ```nginx
    server {
        listen 80;
        server_name padelpro.duckdns.org;

        location / {
            proxy_pass http://127.0.0.1:8080;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```

3.  Guarda el archivo (Ctrl+O, Enter) y sal (Ctrl+X).

4.  Habilita el sitio creando un enlace simbólico:

    ```bash
    sudo ln -s /etc/nginx/sites-available/padelpro /etc/nginx/sites-enabled/
    ```

5.  Verifica que la configuración sea correcta:

    ```bash
    sudo nginx -t
    ```
    *(Debería decir "syntax is ok" y "test is successful")*

6.  Reinicia Nginx para aplicar los cambios:

    ```bash
    sudo systemctl restart nginx
    ```

## 3. Configurar el Firewall (UFW)

Si tienes el firewall activado, necesitas permitir el tráfico HTTP (puerto 80).

```bash
sudo ufw allow 'Nginx Full'
# O específicamente el puerto 80
sudo ufw allow 80
```

## 4. Configurar DuckDNS

Asegúrate de que tu dominio `padelpro.duckdns.org` esté apuntando a tu dirección IP pública actual.

1.  Ve a [DuckDNS](https://www.duckdns.org/).
2.  Inicia sesión y verifica que la IP asociada a `padelpro` sea tu IP pública actual (la puedes ver en sitios como `cualesmiip.com`).
3.  Si tu IP cambia dinámicamente, puedes instalar un script de cron en tu PC para que la actualice automáticamente (instrucciones en la pestaña "install" de DuckDNS).

## 5. Abrir Puertos en el Router (Port Forwarding)

Este paso depende de tu proveedor de internet y marca de router, pero el concepto es el mismo:

1.  Entra a la configuración de tu router (usualmente en `192.168.0.1` o `192.168.1.1`).
2.  Busca la sección de **Port Forwarding**, **Virtual Server** o **Nat Forwarding**.
3.  Crea una nueva regla:
    *   **Puerto Externo (External Port):** 80 y 443
    *   **Puerto Interno (Internal Port):** 80 y 443 (o redirigir ambos a tu IP local)
    *   **Dirección IP Interna (Internal IP):** La IP local de tu PC (ej: `192.168.1.47`).
    *   **Protocolo:** TCP
    *   **Nota:** Necesitas abrir el **puerto 443** también para que funcione HTTPS.

## 6. Probar (Inicial)

1.  Asegúrate de que tu aplicación Flask esté corriendo.
2.  Abre un navegador y entra a:
    `http://padelpro.duckdns.org`
    
    Si esto funciona, ¡podemos pasar al HTTPS!

## 7. Habilitar HTTPS con Certbot

Para obtener un certificado SSL gratuito y asegurar tu conexión, usaremos Certbot.

1.  Instala Certbot y el plugin de Nginx:

    ```bash
    sudo apt install certbot python3-certbot-nginx -y
    ```

2.  Ejecuta Certbot para obtener el certificado y configurar Nginx automáticamente:

    ```bash
    sudo certbot --nginx -d padelpro.duckdns.org
    ```

3.  Sigue las instrucciones en pantalla:
    *   Ingresa tu email (para renovaciones y seguridad).
    *   Acepta los términos de servicio (A).
    *   Si te pregunta si quieres redirigir el tráfico HTTP a HTTPS, elige **2** (Redirect) para que siempre sea seguro.

4.  Certbot modificará automáticamente tu archivo de configuración `/etc/nginx/sites-available/padelpro` para usar SSL.

5.  Verifica la renovación automática:
    ```bash
    sudo certbot renew --dry-run
    ```

https://padelpro.duckdns.org/api/whatsapp/webhook


## 8. Verificación Final

1.  Vuelve a entrar a tu navegador.
2.  Ingresa: `https://padelpro.duckdns.org`
3.  Deberías ver el candado de seguridad 🔒 junto a la URL.

¡Listo! Tu aplicación ahora está expuesta a internet de forma segura.

## 9. Solución de Problemas Comunes

### Error: `DNS problem: SERVFAIL looking up A`
Si Certbot falla con este error, significa que los servidores de Let's Encrypt no pueden encontrar tu IP a través de DuckDNS.
1.  **Verifica tu IP**: Entra a [DuckDNS](https://www.duckdns.org) y asegúrate de que la IP asignada a `padelpro` sea tu IP pública actual (`curl ifconfig.me`).
2.  **Espera**: A veces los cambios de DNS tardan unos minutos en propagarse. Espera 5-10 minutos y vuelve a intentar el comando de Certbot.
3.  **Reinicia el Router**: A veces ayuda a refrescar la conexión y la IP.

### Error: `502 Bad Gateway`
Si al entrar a tu sitio ves este error, significa que Nginx funciona pero no se puede comunicar con tu aplicación Flask.
1.  **Verifica que Flask esté corriendo**: Asegúrate de tener una terminal con `python3 main.py` en ejecución.
2.  **Revisa el puerto**: Asegúrate de que Flask esté en el puerto 8080.

### El sitio no carga (Timeout)
1.  **Port Forwarding**: Revisa que tu router esté redirigiendo el puerto 80 y 443 a la IP local de tu PC.
2.  **Firewall**: Revisa que UFW permita las conexiones (`sudo ufw status`).
