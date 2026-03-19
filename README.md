# TP0: Sistemas Distribuidos I - Cátedra Roca

**Alumno**: Thiago Fernando Baez

**Padrón**: 110703

## Ejercicio 4

El objetivo de este ejercicio es implementar un **graceful shutdown** en cliente y servidor cuando reciben la signal **SIGTERM**.

### Implementación

#### Cliente (`client/common/client.go`)
- **Escucha SIGTERM** mediante un canal de signals
- **Detiene el loop** de envío de mensajes
- **Cierra la conexión** con el servidor
- **Loguea**: `action: sigterm_received | result: success | client_id: X`

#### Servidor (`server/main.py`)
- **Escucha SIGTERM** durante la aceptación de conexiones
- **Cierra sockets** de clientes
- **Loguea el cierre** de cada recurso
- **Timeout**: Respeta el flag `-t` de docker compose

### Flag -t en Docker Compose

```bash
docker compose stop -t 10
```

El flag `-t 10` indica:
- **10 segundos** de grace period (tiempo máximo para graceful shutdown)
- Si la aplicación NO termina en 10s → **SIGKILL** (termina forzadamente)
- El servidor/cliente debe capturar SIGTERM y cerrar recursos **antes** de este timeout

### Logging de Cierre

Durante el shutdown, las aplicaciones emiten logs como:
```
action: sigterm_received | result: success | client_id: 1
action: closing_connection | result: success | client_ip: 172.25.125.3
action: closing_server | result: success | port: 12345
```

Esto permite validar que todos los recursos se cerraron correctamente.

## Permisos de ejecución

Si aparecen errores relacionados con permisos, habilita la ejecución:

```bash
chmod +x validar-echo-server.sh
chmod +x generar-compose.sh
```