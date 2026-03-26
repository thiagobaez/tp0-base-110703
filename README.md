# TP0: Sistemas Distribuidos I - Cátedra Roca

**Alumno**: Thiago Fernando Baez

**Padrón**: 110703

# Ejercicio 7: Sistema de Quinielas - Sincronización de 3 Fases

### Descripción del Problema

Se requiere implementar un servidor de quinielas que:

1. **FASE 1:** Reciba apuestas de **5 agencias diferentes** de forma **secuencial**
2. **FASE 2:** Una vez recibidas TODAS las apuestas, ejecute el sorteo
3. **FASE 3:** Responda consultas de ganadores, pero **solo con ganadores de cada agencia** (privacidad)


## Arquitectura: 3 Fases Secuenciales

### **FASE 1: Recepción de Apuestas**

```python
# En Server.run()
for _ in range(self.num_clients):              # 5 iteraciones
    client_sock = self.__accept_new_connection()
    self.__handle_bets(client_sock)            # ← Bloquea aquí
```

**Flujo temporal:**

```
FASE 1 - TIEMPO LINEAL
━━━━━━━━━━━━━━━━━━━━━━

T0: Servidor esperando conexión...
    Agencia 1 conecta
    ↓
T1-T5: Agencia 1 envía batch 1 → Almacenado en CSV
        → Agencia 1 envía batch 2 → Almacenado en CSV
        → Agencia 1 envía batch 3 → Almacenado en CSV
        → Agencia 1 cierra conexión (EOF)
    ↓
T6: Servidor envía confirmación a Agencia 1
    ↓
T7: Servidor esperando conexión...
    Agencia 2 conecta
    ↓
T8-T12: Agencia 2 envía appuestas
    ↓
T13: Servidor envía confirmación a Agencia 2
    ↓
[Repetir para Agencias 3, 4, 5]
    ↓
T50: Todas las 5 agencias han terminado
```

---

### **FASE 2: Ejecución del Sorteo**

Solo se ejecuta **DESPUÉS** de que FASE 1 termina:

```python
# En Server.run()

for _ in range(self.num_clients):
    client_sock = self.__accept_new_connection()
    self.__handle_bets(client_sock)
    
# ← Todos los clientes han terminado, solo entonces continuamos

self.__perform_lottery()                       # ← FASE 2
```

**Función __perform_lottery():**

```python
def __perform_lottery(self):
    try:
        # 1. Leer TODOS los bets del archivo CSV
        all_bets = list(load_bets())
        
        # 2. Iterar y encontrar ganadores
        winners = []
        for bet in all_bets:
            if has_won(bet):                    
                winners.append((bet.agency, bet.document))
        
        # 3. Guardar en memoria para FASE 3
        self.winners = winners
        
        logging.info(f'action: sorteo | result: success')
        
    except Exception as e:
        logging.error(f"action: sorteo | result: fail | error: {e}")
```

**Archivo CSV después de FASE 1:**

```csv
1,Juan,Perez,12345678,1990-01-01,7574
1,Ana,Garcia,11111111,1995-05-15,999
2,Carlos,Lopez,22222222,1988-12-20,7574
3,Maria,Martinez,33333333,1992-07-10,500
1,Luis,Sanchez,44444444,1999-08-25,7574
4,Pedro,Dias,55555555,1985-03-30,7574
5,Lucia,Torres,66666666,1998-11-12,123
```

**Resultado de sorteo (self.winners):**

```python
self.winners = [
    (1, "12345678"),
    (2, "22222222"),
    (1, "44444444"),
    (4, "55555555"),
]
```

---

### **FASE 3: Consultas Privadas de Ganadores**

```python
# En Server.run()

self.__perform_lottery()                      

for _ in range(self.num_clients):             
    client_sock = self.__accept_new_connection()
    self.__handle_query(client_sock)           # Bloquea aca
```

**Función __handle_query():**

```python
def __handle_query(self, client_sock):
    try:
        # 1. Recibir query del cliente
        is_winner_query, agency_id = receive_query(client_sock)
        
        if is_winner_query:
            # 2. FILTRAR: Solo ganadores de esta agencia
            agency_winners = [dni for (agency, dni) in self.winners 
                             if agency == agency_id]
            
            # 3. Enviar respuesta privada
            send_winners(client_sock, agency_winners)
            
            logging.info(f'action: respuesta_ganadores | result: success | '
                        f'agency_id: {agency_id} | cant_ganadores: {len(agency_winners)}')
    
    except Exception as e:
        logging.error(f"action: receive_query | result: fail | error: {e}")
    finally:
        client_sock.close()
```

**Ejemplo de ejecución FASE 3:**

```
Agencia 1 consulta:
  ├─ Envía: 0x02 + 0x01 (REQUEST_WINNERS para agencia 1)
  ├─ Servidor filtra: [dni for (agency, dni) in self.winners if agency == 1]
  ├─ Resultado: ["12345678", "44444444"]
  └─ Respuesta: 0x03 + size + "12345678,44444444"

Agencia 2 consulta:
  ├─ Envía: 0x02 + 0x02
  ├─ Servidor filtra: [dni for (agency, dni) in self.winners if agency == 2]
  ├─ Resultado: ["22222222"]
  └─ Respuesta: 0x03 + size + "22222222"

Agencia 3 consulta:
  ├─ Envía: 0x02 + 0x03
  ├─ Resultado: [] (sin ganadores)
  └─ Respuesta: 0x03 + size + ""
```

---


## Protocolo Binario de Comunicación

### **FASE 1: Cliente → Servidor**

**Formato de mensaje:**
```
Bytes 0-1: Tamaño del payload (2 bytes, big-endian)
Bytes 2+:  Payload (CSV con apuestas)
```

**Ejemplo: Agencia 1 envía 2 apuestas**
```
┌─────────────┬──────────────────────────────────────────────━┐
│ 0x00 0x5A   │ 1,Juan,Perez,12345678,1990-01-01,7574\n...    │
└─────────────┴──────────────────────────────────────────────━┘
 Size = 90      CSV (90 bytes)
```

**Múltiples batches en la misma conexión:**
```
CONEXIÓN ABIERTA
    ↓
BATCH 1: [0x00][0x2A][...90 bytes CSV...]
    ↓
BATCH 2: [0x00][0x1E][...30 bytes CSV...]
    ↓
BATCH 3: [0x00][0x14][...20 bytes CSV...]
    ↓
CIERRE CONEXIÓN (EOF)
```

**Servidor interpreta EOF como "cliente terminó"**

### **FASE 1: Servidor → Cliente**

**Mensaje de confirmación:**
```
Byte 0: 0x01 (IDX_CONFIRMATION)
Byte 1: 0x01 (éxito) o 0x00 (error)
```

### **FASE 3: Cliente → Servidor**

**Query de ganadores:**
```
Byte 0: 0x02 (IDX_REQUEST_WINNERS)
Byte 1: Agency ID (1 byte)
```

**Ejemplo: Agencia 3 consulta**
```
[0x02] [0x03]
```

### **FASE 3: Servidor → Cliente**

**Lista de ganadores:**
```
Byte 0:    0x03 (IDX_WINNERS_LIST)
Bytes 1-2: Tamaño en bytes (big-endian)
Bytes 3+:  CSV "dni1,dni2,dni3,..."
```

**Ejemplo: Agencia 1 recibe 2 ganadores**
```
┌────────┬───────────────┬──────────────────┐
│ 0x03   │ 0x00 0x17     │12345678,44444444 │
└────────┴───────────────┴──────────────────┘
         Size = 23 bytes   (17 hex = 23 dec)
```
