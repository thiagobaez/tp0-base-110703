import csv
import datetime
import time


""" Bets storage location. """
STORAGE_FILEPATH = "./bets.csv"
""" Simulated winner number in the lottery contest. """
LOTTERY_WINNER_NUMBER = 7574

CANT_BYTES_HEADER = 2

IDX_AGENCY = 0
IDX_FIRST_NAME = 1
IDX_LAST_NAME = 2
IDX_DNI = 3
IDX_BIRTHDATE = 4
IDX_NUMBER = 5

IDX_CONFIRMATION = 0x01
IDX_CONFIRMATION_SUCCESS = 0x01
IDX_CONFIRMATION_FAIL = 0x00
IDX_REQUEST_WINNERS = 0x02
IDX_WINNERS_LIST = 0x03  # Header para lista de ganadores


""" A lottery bet registry. """
class Bet:
    def __init__(self, agency: str, first_name: str, last_name: str, document: str, birthdate: str, number: str):
        """
        agency must be passed with integer format.
        birthdate must be passed with format: 'YYYY-MM-DD'.
        number must be passed with integer format.
        """
        self.agency = int(agency)
        self.first_name = first_name
        self.last_name = last_name
        self.document = document
        self.birthdate = datetime.date.fromisoformat(birthdate)
        self.number = int(number)

""" Checks whether a bet won the prize or not. """
def has_won(bet: Bet) -> bool:
    return bet.number == LOTTERY_WINNER_NUMBER

"""
Persist the information of each bet in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def store_bets(bets: list[Bet]) -> None:
    with open(STORAGE_FILEPATH, 'a+') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
        for bet in bets:
            writer.writerow([bet.agency, bet.first_name, bet.last_name,
                             bet.document, bet.birthdate, bet.number])

"""
Loads the information all the bets in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def load_bets() -> list[Bet]:
    with open(STORAGE_FILEPATH, 'r') as file:
        reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            yield Bet(row[0], row[1], row[2], row[3], row[4], row[5])


def receive_bytes_from_socket(client_socket) -> bytes:

    tam_buffer = int.from_bytes(recvall(client_socket, CANT_BYTES_HEADER), byteorder='big')
    return recvall(client_socket, tam_buffer)


def decode_bets(client_sock) -> list[Bet]:

    bytes_received = receive_bytes_from_socket(client_sock)

    bets_string = bytes_received.decode('utf-8')
    
    lines = bets_string.strip().split('\n')
    
    bets = []
    for line in lines:
        if line.strip():
            fields = line.split(',')
            bet = Bet(
                agency=fields[IDX_AGENCY],
                first_name=fields[IDX_FIRST_NAME],
                last_name=fields[IDX_LAST_NAME],
                document=fields[IDX_DNI],
                birthdate=fields[IDX_BIRTHDATE],
                number=fields[IDX_NUMBER]
            )
            bets.append(bet)
    
    return bets

def receive_query(client_sock) -> tuple:
    header = recvall(client_sock, 1)

    if header == IDX_REQUEST_WINNERS.to_bytes(1, byteorder='big'):
        agency_id_byte = recvall(client_sock, 1)
        agency_id = int.from_bytes(agency_id_byte, byteorder='big')
        return (True, agency_id)

    return (False, None)


def send_confirmation(client_sock, operation_success: bool):

    message = IDX_CONFIRMATION.to_bytes(1, byteorder='big')

    if operation_success:
        message += IDX_CONFIRMATION_SUCCESS.to_bytes(1, byteorder='big')
    else:
        message += IDX_CONFIRMATION_FAIL.to_bytes(1, byteorder='big')

    sendall(client_sock, message)

def send_winners(client_sock, winners: list[str]):

    winners_csv = ','.join(winners)
    message_bytes = winners_csv.encode('utf-8')
    tam_buffer = len(message_bytes)
    
    # Construir: header (0x03) + tamaño (2 bytes) + DNIs
    response_header = IDX_WINNERS_LIST.to_bytes(1, byteorder='big')
    size_header = tam_buffer.to_bytes(2, byteorder='big')
    sendall(client_sock, response_header + size_header + message_bytes)


def recvall(client_sock, n) -> bytes:
    buffer = bytearray()
    while len(buffer) < n: # Aseguro que no se produzca un short-read
        bytes_received = client_sock.recv(n - len(buffer))
        if not bytes_received:
            raise ConnectionError("Connection closed by the client.")
        buffer.extend(bytes_received)
    return bytes(buffer)

def sendall(client_sock, message):

    if isinstance(message, str):
        message_bytes = message.encode('utf-8')
    else:
        message_bytes = message
    tam_buffer = len(message_bytes)
    
    bytes_sent = 0
    while bytes_sent < tam_buffer: # Aseguro que no se produzca un short-write
        sent = client_sock.send(message_bytes[bytes_sent:])
        if sent == 0:
            raise ConnectionError("Connection closed by the client.")
        bytes_sent += sent














