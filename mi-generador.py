import sys

INDEX_OUTPUT_FILENAME = 1
INDEX_NUMBER_OF_CLIENTS = 2

CONTAINER_NAME = "tp0"

SERVER_SERVICE_NAME = "server"
SERVER_CONTAINER_NAME = "server"
SERVER_IMAGE = "server:latest"
SERVER_ENTRYPOINT = "python3 /main.py"
SERVER_ENVIRONMENT_VARIABLES = {
    "PYTHONUNBUFFERED": "1",
    "LOGGING_LEVEL": "DEBUG"
}

CLIENT_SERVICE_NAME = "client"
CLIENT_CONTAINER_NAME_PREFIX = "client"
CLIENT_IMAGE = "client:latest"
CLIENT_ENTRYPOINT = "/client"
CLIENT_ENV_LOG_LEVEL = "DEBUG"

NETWORK = "testing_net"
NETWORK_DRIVER = "default"
NETWORK_SUBNET = "172.25.125.0/24"


def docker_compose_generate(output_filename: str, number_of_clients: int):
    with open(output_filename, 'w') as f:
        f.write(f"name: {CONTAINER_NAME}\n")
        f.write("services:\n")
        
        # Definir el servicio del servidor
        f.write(f"  {SERVER_SERVICE_NAME}:\n")
        f.write(f"    container_name: {SERVER_CONTAINER_NAME}\n")
        f.write(f"    image: {SERVER_IMAGE}\n")
        f.write(f"    entrypoint: {SERVER_ENTRYPOINT}\n")
        f.write("    environment:\n")
        for key, value in SERVER_ENVIRONMENT_VARIABLES.items():
            f.write(f"      - {key}={value}\n")
        f.write("    networks:\n")
        f.write(f"      - {NETWORK}\n")
        f.write("\n")
        
        # Definir los servicios de los clientes
        for i in range(1, number_of_clients + 1):
            client_service_name = f"{CLIENT_SERVICE_NAME}{i}"
            client_container_name = f"{CLIENT_CONTAINER_NAME_PREFIX}{i}"
            f.write(f"  {client_service_name}:\n")
            f.write(f"    container_name: {client_container_name}\n")
            f.write(f"    image: {CLIENT_IMAGE}\n")
            f.write(f"    entrypoint: {CLIENT_ENTRYPOINT}\n")
            f.write("    environment:\n")
            f.write(f"      - CLI_ID={i}\n")
            f.write(f"      - LOG_LEVEL={CLIENT_ENV_LOG_LEVEL}\n")
            f.write("    networks:\n")
            f.write(f"      - {NETWORK}\n")
            f.write("    depends_on:\n")
            f.write(f"      - {SERVER_SERVICE_NAME}\n")
            f.write("\n")

        # Definir la red
        f.write("networks:\n")
        f.write(f"  {NETWORK}:\n")
        f.write("    ipam:\n")
        f.write(f"      driver: {NETWORK_DRIVER}\n")
        f.write("      config:\n")
        f.write(f"        - subnet: {NETWORK_SUBNET}\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Use: python mi-generador.py <output_filename> <number_of_clients>")
        sys.exit(1)

    output_filename = sys.argv[INDEX_OUTPUT_FILENAME]
    number_of_clients = int(sys.argv[INDEX_NUMBER_OF_CLIENTS])

    docker_compose_generate(output_filename, number_of_clients)
    print(f"'{output_filename}' successfully generated with {number_of_clients} clients.")