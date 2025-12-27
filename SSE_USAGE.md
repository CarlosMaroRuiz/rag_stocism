# Server-Sent Events (SSE) - Sistema de Recomendaciones Estoicas

## 🌊 ¿Qué es SSE?

Server-Sent Events (SSE) es una tecnología que permite al servidor enviar actualizaciones en tiempo real al cliente a través de una conexión HTTP persistente. A diferencia de WebSockets, SSE es unidireccional (solo servidor → cliente) y usa HTTP estándar.

## 📡 Endpoints Disponibles

### 1. POST `/generate/recommendations` (Tradicional)
- **Tipo**: Request/Response estándar
- **Ventaja**: Simple, respuesta completa al final
- **Desventaja**: Usuario espera sin feedback hasta que todo termine
- **Uso**: Para integraciones donde no importa el tiempo de espera

```bash
curl -X POST http://localhost:8000/generate/recommendations \
  -H "Content-Type: application/json" \
  -d '{"user_id": "7e41ec3e-344a-42d4-8aba-f75196098e10"}'
```

### 2. GET `/generate/recommendations/stream` (SSE) ⭐ **RECOMENDADO**
- **Tipo**: Server-Sent Events (streaming)
- **Ventaja**: Feedback en tiempo real, cada recomendación se muestra conforme se genera
- **Desventaja**: Requiere manejo de eventos en el cliente
- **Uso**: Para interfaces de usuario donde la experiencia importa

```bash
curl -N http://localhost:8000/generate/recommendations/stream?user_id=7e41ec3e-344a-42d4-8aba-f75196098e10
```

## 🎯 Eventos Emitidos por el Endpoint SSE

### 1. `status` - Estado del proceso
```json
{
  "message": "Obteniendo perfil estoico del usuario..."
}
```

### 2. `profile` - Perfil del usuario
```json
{
  "summary": "Usuario 18-25 | ocasional | Nivel estoico: principiante | Caminos: Paz Interior, Autocontrol",
  "topic": "estoicismo"
}
```

### 3. `recommendation` - Cada recomendación individual
```json
{
  "index": 1,
  "total": 5,
  "title": "La Dicotomía del Control",
  "content": "Explicación detallada de la enseñanza...",
  "source_reference": "Marco Aurelio, Meditaciones, Libro II",
  "difficulty": "fácil"
}
```

### 4. `complete` - Finalización exitosa
```json
{
  "message": "Recomendaciones completadas",
  "total": 5
}
```

### 5. `error` - Error durante el proceso
```json
{
  "error": "Descripción del error"
}
```

## 💻 Uso desde JavaScript (Frontend)

```javascript
const eventSource = new EventSource(
  'http://localhost:8000/generate/recommendations/stream?user_id=USER_ID'
);

// Escuchar eventos
eventSource.addEventListener('status', (event) => {
  const data = JSON.parse(event.data);
  console.log('Estado:', data.message);
});

eventSource.addEventListener('profile', (event) => {
  const data = JSON.parse(event.data);
  console.log('Perfil:', data.summary);
});

eventSource.addEventListener('recommendation', (event) => {
  const rec = JSON.parse(event.data);
  console.log(`Recomendación ${rec.index}/${rec.total}:`, rec.title);
  // Mostrar en UI con animación
});

eventSource.addEventListener('complete', (event) => {
  const data = JSON.parse(event.data);
  console.log('Completado:', data.total, 'recomendaciones');
  eventSource.close(); // Cerrar conexión
});

eventSource.addEventListener('error', (event) => {
  const data = JSON.parse(event.data);
  console.error('Error:', data.error);
  eventSource.close();
});

// Error de conexión
eventSource.onerror = (error) => {
  console.error('Error de conexión:', error);
  eventSource.close();
};
```

## 🧪 Pruebas

### Prueba Directa (Controller)
```bash
python test.py
```

### Prueba Endpoint SSE (requiere servidor corriendo)
```bash
# Terminal 1: Iniciar servidor
uvicorn main:app --reload

# Terminal 2: Probar SSE
python test.py --sse
```

### Prueba desde el Frontend
1. Abre `index.html` en tu navegador
2. Selecciona un usuario de prueba
3. Haz clic en "Recibir Enseñanzas Estoicas"
4. Observa cómo cada recomendación aparece con animación en tiempo real

## 🎨 Ventajas del Enfoque SSE

### ✅ Experiencia de Usuario
- **Feedback inmediato**: El usuario ve el progreso en tiempo real
- **Animaciones suaves**: Cada recomendación aparece con transición
- **Indicador de progreso**: "Recibiendo enseñanza 2 de 5..."
- **Menos ansiedad**: Usuario sabe que algo está pasando

### ✅ Técnicas
- **HTTP estándar**: No requiere WebSockets
- **Reconexión automática**: EventSource reconecta si se pierde conexión
- **Compatible con proxies**: Funciona con nginx, Apache, etc.
- **Cacheable**: Puede usar CDN si es necesario

### ✅ Desarrollo
- **Simple de implementar**: Usa `StreamingResponse` de FastAPI
- **Fácil de debuggear**: Eventos en formato texto plano
- **Compatible con navegadores**: Soporte nativo en todos los navegadores modernos

## 🔧 Configuración del Servidor

### FastAPI (ya implementado)
```python
from fastapi.responses import StreamingResponse

async def event_generator():
    yield f"event: status\ndata: {json.dumps({'message': 'Procesando...'})}\n\n"
    # ... más eventos

return StreamingResponse(
    event_generator(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"  # Importante para nginx
    }
)
```

### Nginx (si usas reverse proxy)
```nginx
location /generate/recommendations/stream {
    proxy_pass http://backend;
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding off;
    proxy_buffering off;
    proxy_cache off;
}
```

## 🐛 Debugging

### Ver eventos en consola del navegador
```javascript
eventSource.onmessage = (event) => {
  console.log('Raw event:', event);
};
```

### Ver eventos con curl
```bash
curl -N http://localhost:8000/generate/recommendations/stream?user_id=USER_ID
```

### Logs del servidor
El controller imprime información de debug:
- `🔍 DEBUG - Raw LLM Response`
- `✅ DEBUG - JSON limpio`
- `⚠️ DEBUG - JSON encontrado en posición X`

## 📚 Referencias

- [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [EventSource API](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
