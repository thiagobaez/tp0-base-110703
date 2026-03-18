# TP0: Sistemas Distribuidos I - Cátedra Roca

**Alumno**: Thiago Fernando Baez

**Padrón**: 110703

## Ejercicio 1
 

El objetivo de este ejercicio es cambiar el comportamiento del Cliente y el Servidor para que los archivos de configuración no queden dentro de la imagen, sino que se mantengan de forma externa.

Para lograrlo, se incorporaron volúmenes en los archivos docker-compose-dev.yaml y mi-generador.py, permitiendo que la configuración se almacene y persista fuera de los contenedores.

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