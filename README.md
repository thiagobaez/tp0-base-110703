# TP0: Sistemas Distribuidos I - Cátedra Roca

**Alumno**: Thiago Fernando Baez

**Padrón**: 110703

## Ejercicio 5: Sistema de Quinielas Distribuido

### Descripción General

Este ejercicio implementa un sistema de gestión de apuestas de quinielas distribuido entre clientes (agencias) y un servidor central (Lotería Nacional). Los clientes envían apuestas al servidor, quien las almacena y persiste en una base de datos CSV.

### Campos de la Apuesta

Cada apuesta contiene:
- **Agencia**: ID de la agencia (extraído del config del cliente)
- **Nombre**: Nombre de la persona
- **Apellido**: Apellido de la persona
- **DNI**: Documento de identidad (sin dígito verificador)
- **Nacimiento**: Fecha de nacimiento (formato ISO: YYYY-MM-DD)
- **Número**: Número apostado (entero)

### Protocolo de Comunicación

#### Formato del Mensaje

```
[Header (2 bytes)][Payload (N bytes)]
```

- **Header**: Tamaño del payload en big-endian (16 bits)
- **Payload**: Datos serializados separados por comas (CSV)

#### Ejemplo de Datos Serializados
```
1,Thiago,Baez,44555543,2003-02-11,592
```

#### Confirmación del Servidor

```
[Tipo (1 byte)][Estado (1 byte)]
```

- **Tipo**: `0x01` (mensaje de confimación de apuesta)
- **Estado**: 
  - `0x01` → Éxito
  - `0x00` → Error en el servidor

### Compilación y Ejecución

#### Prerrequisitos
- Docker y Docker Compose

#### Comando de Ejecución

```bash
# Iniciar contenedores
make docker-compose-up

# Ver logs en tiempo real
make docker-compose-logs

# Detener contenedores
make docker-compose-down
```


### Implementación Detallada

#### Lado Cliente (Go)

**`client/common/bet.go`**
- `sendall()`: Implementa la lógica de short-write evitando pérdida de datos
- `recvall()`: Implementa la lógica de short-read asegurando recepción completa
- `sendMessage()`: Serializa datos con encabezado de tamaño
- `sendBet()`: Formatea una apuesta como string CSV
- `receiveMessage()`: Recibe y valida confirmación del servidor

**`client/common/client.go`**
- `StartClientLoop()`: Loop principal que envía apuestas repetidamente
- Logging estructurado con niveles (INFO, CRITICAL)

#### Lado Servidor (Python)

**`server/common/utils.py`**
- `Bet`: Clase que representa una apuesta
- `recvall()`: Implementa recepción completa de datos
- `sendall()`: Implementa envío completo de datos
- `receive_bytes_from_socket()`: Lee header y payload
- `decode_bet()`: Parsea CSV a objeto Bet
- `send_confirmation()`: Envía respuesta binaria al cliente
- `store_bets()`: Persiste apuestas en CSV (función proporcionada por cátedra)

**`server/common/server.py`**
- `run()`: Loop de aceptación de conexiones
- `__handle_client_connection()`: Procesa una apuesta y envía confirmación

### Aspectos Técnicos Implementados

#### Manejo de Errores
- Validación de formato de datos
- Detección de desconexiones abruptas
- Manejo de errores de I/O en sockets

#### Short Read/Write
- Loops en `sendall()` y `recvall()` aseguran envío/recepción completa
- Evita pérdida de datos por buffers parciales del SO

#### Serialización
- Datos serializados como CSV para facilitar parseo y persistencia
- Encabezado de tamaño (2 bytes) precede cada mensaje