#!/bin/bash

echo "Nombre del archivo de salida: $1"
echo "Cantidad de clientes: $2"
# Ejecuta el script de Python generado pasando como parámetros el archivo y la cantidad de clientes.
python3 mi-generador.py $1 $2