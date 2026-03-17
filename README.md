# TP0: Sistemas Distribuidos I - Cátedra Roca

**Alumno**: Thiago Fernando Baez

**Padrón**: 110703

## Ejercicio 1
 

El propósito de este ejercicio es desarrollar un script en Bash llamado `generar-compose.sh`, cuya función será automatizar la creación de un archivo `.yaml` con la configuración necesaria para un entorno de Docker Compose.

El archivo generado deberá contemplar:

- Un servicio que actuará como servidor.
- Un número **N** de servicios cliente.
- Una red compartida que permita la comunicación entre todos los servicios.

El script Bash funcionará como intermediario, delegando la generación del contenido del archivo al programa `mi-generador.py`, que será el encargado de construir la estructura final del YAML.

Este script podrá ser modificado o ampliado en ejercicios posteriores, incorporando nuevas funcionalidades según los requerimientos.

## Permisos de ejecución

Si aparecen errores relacionados con permisos al intentar ejecutar el script, es necesario habilitar su ejecución con el siguiente comando:

```bash
chmod +x generar-compose.sh
```

## Uso

Para ejecutar el script:

```bash
./generar-compose.sh <output_filename> <number_of_clients>
```

## Como usar la salida generada

Una vez que se generó el archivo, se puede usar para desplegar el entorno usando el Makefile del proyecto:

```bash
make docker-compose-up
```

Aclaración: el nombre del archivo generado debe ser `docker-compose-dev.yaml`. Si se quiere usar otro con el makefile, hay que modificar el mismo.
