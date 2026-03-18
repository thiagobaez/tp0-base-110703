# TP0: Sistemas Distribuidos I - Cátedra Roca

**Alumno**: Thiago Fernando Baez

**Padrón**: 110703

## Ejercicio 3

El objetivo de este ejercicio es crear un script de validación que verifique el correcto funcionamiento del servidor echo sin necesidad de instalar herramientas adicionales en la máquina host.

### Script: `validar-echo-server.sh`

El script `validar-echo-server.sh` ubicado en la raíz del proyecto permite verificar que el servidor echo funciona correctamente:

**Características:**
- Utiliza **netcat** (nc) para comunicarse con el servidor
- **No requiere instalar netcat** en la máquina host (se ejecuta dentro de un container Alpine)
- **No expone puertos** del servidor en el host (usa la red interna docker: `tp0_testing_net`)
- Envía un mensaje de prueba (`hello`) y verifica que reciba el mismo mensaje como respuesta

**Funcionamiento:**
1. Crea un container temporal de Alpine conectado a la red `tp0_testing_net`
2. Envía el mensaje `hello` al servidor a través de netcat con timeout de 2 segundos
3. Limpia caracteres de control (\r\n) de la respuesta
4. Compara la respuesta con el mensaje esperado

**Salida:**
- Si la validación es exitosa: `action: test_echo_server | result: success`
- Si falla: `action: test_echo_server | result: fail`

**Uso:**
```bash
./validar-echo-server.sh
```

**Requisitos previos:**
- El docker-compose debe estar ejecutándose: `make docker-compose-up`
- La red `tp0_testing_net` debe estar activa

## Permisos de ejecución

Si aparecen errores relacionados con permisos, habilita la ejecución:

```bash
chmod +x validar-echo-server.sh
chmod +x generar-compose.sh
```