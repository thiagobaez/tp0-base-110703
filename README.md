# TP0: Sistemas Distribuidos I - Cátedra Roca

**Alumno**: Thiago Fernando Baez

**Padrón**: 110703

---

## Ejercicio 6: Procesamiento por Batches (Chunks) y Persistencia en Volúmenes

### Descripción General

Se modificó el sistema de quinielas para que los clientes envíen múltiples apuestas en un solo mensaje (batch/chunk), mejorando eficiencia en transmisión y procesamiento. Las apuestas se cargan desde archivos CSV proporcionados por la cátedra, injectados mediante Docker volumes.

### Cambios Principales

#### 1. **Carga de Apuestas desde Archivo (Cliente)**

El cliente carga todas las apuestas de un archivo CSV en memoria al iniciar:

```go
func loadBetsFromFile(id string) ([]Bet, error) {
    file, err := os.Open("agency.csv")
    if err != nil {
        log.Errorf("action: open_csv_file | result: fail | client_id: %v | error: %v", id, err)
        return []Bet{}, err
    }

    reader := csv.NewReader(file)
    records, err := reader.ReadAll()
    if err != nil {
        return []Bet{}, err
    }

    bets := []Bet{}
    for _, record := range records {
        bet := Bet{
            AgencyId:  id,                  // ID de la agencia
            Name:      record[0],
            Lastname:  record[1],
            Dni:       record[2],
            Birthdate: record[3],
            Number:    record[4],
        }
        bets = append(bets, bet)
    }
    file.Close()
    return bets, nil
}
```

**Nombre del archivo:** `agency.csv` (dentro del container)

**Estructura esperada en el archivo:**
```csv
Juan,Perez,12345678,1990-01-01,7574
Ana,Garcia,11111111,1995-05-15,999
Carlos,Lopez,22222222,1988-12-20,7574
...
```

#### 2. **Docker Volumes para Persistencia**

Se configuran volúmenes en `docker-compose-dev.yaml` para mapear los datasets hacia containers:

```yaml
services:
  client_1:
    volumes:
      - ./.data/agency-1.csv:/app/agency.csv

  client_2:
    volumes:
      - ./.data/agency-2.csv:/app/agency.csv

  client_3:
    volumes:
      - ./.data/agency-3.csv:/app/agency.csv
  # ... client 4 y 5
```

**Mapeo:**
```
HOST                      CONTAINER
.data/agency-1.csv   →    /app/agency.csv
.data/agency-2.csv   →    /app/agency.csv
.data/agency-3.csv   →    /app/agency.csv
```

**Ventajas:**
- Archivos de datos permanecen en host (fuera del container)
- Cada cliente recibe su dataset correcto
- Fácil actualizar datos sin reconstruir imágenes

#### 3. **Envío en Batches con Límites Duales (Cliente)**

El cliente divide las apuestas en batches respetando **dos criterios simultáneamente:**

```go
func sendBets(conn net.Conn, bets []Bet, maxBatchAmount int) error {
    i := 0
    for i < len(bets) {
        message := ""
        betsInBatch := 0
        
        for i < len(bets) && betsInBatch < maxBatchAmount {
            bet := bets[i]
            betLine := fmt.Sprintf("%s,%s,%s,%s,%s,%s\n",
                bet.AgencyId,
                bet.Name,
                bet.Lastname,
                bet.Dni,
                bet.Birthdate,
                bet.Number,
            )
            
            // Criterio 1: Revisar tamaño en bytes
            if len(message)+len(betLine) > MAX_BATCH_SIZE_BYTES && betsInBatch > 0 {
                break  // Ya tenemos suficientes, enviar este batch
            }
            
            message += betLine
            betsInBatch++  // Criterio 2: Contador de apuestas
            i++
        }
        
        if err := sendMessage(conn, message); err != nil {
            return err
        }
    }

    // Enviar mensaje vacío para señalizar EOF
    if err := sendMessage(conn, ""); err != nil {
        return err
    }

    return nil
}
```

**Constantes definidas:**
```go
const (
    LENGTH_HEADER        = 2
    MAX_MESSAGE_SIZE     = 1024
    MAX_BATCH_SIZE_BYTES = 8192  // 8 KB máximo
)
```

#### 4. **Configuración en config.yaml**

```yaml
batch:
  maxAmount: 172
```

**Cálculo del tamaño máximo de apuestas por batch:**

Para que un batch no exceda 8 KB:
```
8.192 bytes / aprox. 47 bytes por apuesta ≈ 174 apuestas máximo
```

**Tamaño de una apuesta (ejemplo):**
```csv
1,Juan,Perez,12345678,1990-01-01,7574
```
Aprox. 47 bytes + 1 byte de newline = 48 bytes por apuesta

#### 5. **Protocolo de Envío de Batches**

**Cliente → Servidor (cada batch):**
```
┌──────────────┬─────────────────────────┐
│ Header (2B)  │ Payload (CSV multi-row) │
├──────────────┼─────────────────────────┤
│ 0x00 0x2A    │ 1,Juan,Perez,...        │
│ (42 bytes)   │ 1,Ana,Garcia,...        │
│              │ 1,Carlos,Lopez,...      │
└──────────────┴─────────────────────────┘
```

**Múltiples batches en una conexión:**
```
CONEXIÓN ABIERTA
    ↓
BATCH 1: [0x1E][172 apuestas CSV]
    ↓
BATCH 2: [0x1E][172 apuestas CSV]
    ↓
BATCH 3: [0x18][156 apuestas CSV]
    ↓
BATCH N: [0x00][] ← Mensaje vacío (EOF)
    ↓
CIERRE CONEXIÓN
```

#### 6. **Procesamiento de Batches en el Servidor**

```python
def __handle_client_connection(self, client_sock):
    try:
        while True:
            try:
                bets = decode_bets(client_sock)
                if not bets:     
                    break
                store_bets(bets)     
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
            except ConnectionError:
                break
        
        send_confirmation(client_sock, True)
        
    except Exception as e:
        logging.error(f"action: apuesta_recibida | result: fail | cantidad: {len(bets)}")
```

**Función decode_bets():**
```python
def decode_bets(client_sock) -> list[Bet]:
    bytes_received = receive_bytes_from_socket(client_sock)
    
    bets_string = bytes_received.decode('utf-8')
    lines = bets_string.strip().split('\n')
    
    bets = []
    for line in lines:
        if line.strip():
            fields = line.split(',')
            bet = Bet(
                agency=fields[0],
                first_name=fields[1],
                last_name=fields[2],
                document=fields[3],
                birthdate=fields[4],
                number=fields[5]
            )
            bets.append(bet)
    
    return bets  # Retorna LISTA (batch completo)
```

#### 7. **Manejo de Confirmaciones**

**Servidor → Cliente:**
```
[0x01][0x01]  ← Éxito (0x01 = sucesso)
[0x01][0x00]  ← Error  (0x00 = fallo)
```

**Garantía:**
- La confirmación se envía solo una vez, después de procesar todos los batches
- Si cualquier batch falla, se retorna error
- Si todos se procesan correctamente, se retorna éxito

---