# TP0: Sistemas Distribuidos I - Cátedra Roca

**Alumno**: Thiago Fernando Baez

**Padrón**: 110703

## Ejercicio 8

## Descripción General

Se ha modificado el servidor para que acepte conexiones y procese mensajes de múltiples clientes **en paralelo** utilizando multithreading en lugar del modelo secuencial. El servidor ahora puede manejar varias agencias simultáneamente, mejorando significativamente la concurrencia del sistema.

---

## Cambios Principales Realizados

### 1. **Introducción de Threading**

#### Importaciones Agregadas
```python
import threading
import time
```

Se incorporó el módulo `threading` para crear y gestionar múltiples hilos de ejecución de forma paralela.

#### Variables de Control de Sincronización
```python
self.lock = threading.Lock()
self.phase_1_done = threading.Condition(self.lock)
self._shutdown_event = threading.Event()
self._active_threads = []
```

**Propósito de cada mecanismo:**
- `self.lock`: Mutex para proteger acceso a variables compartidas
- `self.phase_1_done`: Condition variable para sincronización entre fases
- `self._shutdown_event`: Señal para cierre graceful del servidor
- `self._active_threads`: Lista para rastrear todos los hilos activos

---

## Estructura del Servidor: Tres Fases

### **FASE 1: Recepción de Apuestas (Paralela)**

```
┌─────────────────────────────────────┐
│   Aceptar conexiones en bucle       │
├─────────────────────────────────────┤
│ Para cada agencia:                  │
│  ├─ Crear nuevo Thread              │
│  ├─ Procesar apuestas concurrently  │
│  └─ Almacenarlas en CSV             │
└─────────────────────────────────────┘
        ↓
Esperar condition variable (todas terminen)
        ↓
   FASE 2
```

**Código:**
```python
while client_count < self.num_clients and not self._shutdown_event.is_set():
    client_sock = self.__accept_new_connection()
    
    client_thread = threading.Thread(
        target=self.__handle_client_connection,
        args=(client_sock,)
    )
    self._active_threads.append(client_thread)
    client_thread.start()
    client_count += 1
```

**Qué sucede en cada thread:**
- Recibe apuestas del cliente
- Almacena cada lote en CSV
- Notifica al servidor cuando término

---

### **FASE 2: Ejecución de la Lotería (Secuencial)**

```
Fase 1 completada (todos los threads finalizados)
        ↓
Cargar todas las apuestas del CSV
        ↓
Iterar y encontrar ganadores
        ↓
Guardar lista de ganadores en memoria
```

**Por qué es secuencial:** No pueden haber más apuestas mientras se ejecuta la lotería.

---

### **FASE 3: Consultas de Ganadores (Paralela)**

```
Lotería completada (sorteo_completed = True)
        ↓
┌──────────────────────────────────┐
│ Aceptar nuevas conexiones        │
├──────────────────────────────────┤
│ Para cada agencia:               │
│  ├─ Criar nuevo Thread           │
│  ├─ Recibir query de ganadores   │
│  └─ Enviar respuesta             │
└──────────────────────────────────┘
        ↓
Esperar que todos terminen
```

---

## Mecanismos de Sincronización Implementados

### 1. **Lock (Mutex) - threading.Lock()**

**Uso:** Proteger secciones críticas

```python
self.lock = threading.Lock()
```

Garantiza que solo un thread pueda ejecutar cierta sección de código a la vez.

### 2. **Condition Variable - threading.Condition()**

**Uso:** Sincronización entre fase 1 y fase 2

**Es más eficiente que polling** porque:
- Los threads se ponen en espera (no consumen CPU)
- Se despiertan automáticamente cuando todos han terminado
- Evita busy-waiting

### 3. **Event - threading.Event()**

**Uso:** Cierre graceful del servidor

```python
self._shutdown_event = threading.Event()

def __handle_shutdown(self, signum, frame):
    self._shutdown_event.set()
    self._server_socket.close()
```

Los threads verifican periódicamente si deben detener su ejecución:
```python
while client_count < self.num_clients and not self._shutdown_event.is_set():
    # continuar aceptando conexiones
```

---


### **Lista de Ganadores**

```python
self.winners = []  # Variable compartida
```

- Se modifica en FASE 2 (un solo thread ejecuta `__perform_lottery()`)
- Se lee en FASE 3 (protegida por sincronización de fases)
- Acceso seguro porque no hay race condition

---


## Flujo de Ejecución Completo

```
┌─────────────────────────────────┐
│  Inicio del Servidor            │
│  (thread principal)             │
└─────────────────────┬───────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
    ┌────▼────┐            ┌──────▼──────┐
    │ FASE 1  │            │   espera    │
    │ Aceptar │            │ condition   │
    │ threads │            └──────┬──────┘
    └────┬────┘                  │
         │         ┌─────────────┘
    ┌────▼────────┐
    │Todos los    │
    │threads      │
    │finalizaron  │
    └────┬────────┘
         │
    ┌────▼────────┐
    │FASE 2       │
    │Ejecutar     │
    │Lotería      │
    └────┬────────┘
         │
    ┌────▼────────────┐
    │FASE 3           │
    │Aceptar queries  │
    │en paralelo      │
    └────┬────────────┘
         │
    ┌────▼────────────┐
    │ Servidor        │
    │ Finalizado      │
    └─────────────────┘
```
