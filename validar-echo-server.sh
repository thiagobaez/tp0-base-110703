#!/bin/bash

# Script para validar que el servidor echo funciona correctamente
# Usa netcat desde un container temporal sin instalar nada en el host
# Se conecta a través de la red de docker-compose

SET_MESSAGE="TestMessage123"

# Envía el mensaje al servidor usando netcat en un container temporal
# conectado a la red del docker-compose (tp0_testing_net)
RESPONSE=$(echo "$SET_MESSAGE" | docker run --rm --network tp0_testing_net -i busybox nc -w 1 server 12345 2>/dev/null)

# Valida que la respuesta sea igual al mensaje enviado
if [ "$RESPONSE" = "$SET_MESSAGE" ]; then
	echo "action: test_echo_server | result: success"
	exit 0
else
	echo "action: test_echo_server | result: fail"
	exit 1
fi

