# TP0: Sistemas Distribuidos I - Cátedra Roca

**Alumno**: Thiago Fernando Baez

**Padrón**: 110703

---

## Ejercicio 2: Configuración Inyectada mediante Docker Volumes

### Descripción del Problema

**Sin Ejercicio 2 (Base):**
- Cambiar `config.ini` o `config.yaml` requiere reconstruir la imagen Docker con `docker build`
- Las imágenes tienen la configuración hardcodeada en el momento del build
- Modificar parámetros implica: stop → build → up (proceso lento)

**Con Ejercicio 2:**
- Los archivos de configuración se inyectan en tiempo de ejecución
- Modificar configuración solo requiere cambiar el archivo y reiniciar el container
- No es necesario reconstruir la imagen

### Solución: Docker Volumes

Se mapean archivos de configuración del HOST hacia los containers usando volúmenes:

#### **Servidor (Python)**

**Archivo necesario en HOST:**
```
./server/config.ini
```


**Mapeo en docker-compose-dev.yaml:**
```yaml
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    volumes:
      - ./server/config.ini:/config.ini:ro
    networks:
      - testing_net
```

**Cómo funciona:**
1. El servidor se inicia en el container
2. Lee `/config.ini` desde el container (que es un mount del HOST)
3. El servidor interpreta las variables de configuración

#### **Cliente (Go)**

**Archivo necesario en HOST:**
```
./client/config.yaml
```

**Mapeo en docker-compose-dev.yaml:**
```yaml
services:
  client1:
    container_name: client1
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID=1
      - CLI_LOG_LEVEL=DEBUG
    volumes:
      # HOST PATH          CONTAINER PATH     FLAGS
      - ./client/config.yaml:/config.yaml
    networks:
      - testing_net
    depends_on:
      - server
```

**Para múltiples clientes:**
```yaml
  client1:
    volumes:
      - ./client/config.yaml:/config.yaml

  client2:
    volumes:
      - ./client/config.yaml:/config.yaml

  client3:
    volumes:
      - ./client/config.yaml:/config.yaml
  # ... etc
```

#### Generar el archivo `docker-compose-dev.yaml`

```bash
./generar-compose.sh <output-filename.yaml> <num_of_clients>
```


