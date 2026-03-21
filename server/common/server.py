import socket
import logging
import signal
import threading
from .utils import Bet, decode_bets, store_bets, send_confirmation, load_bets, has_won, sendall
class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.agencies_finished_count = 0
        self.sorteo_completed = False
        self.winners = []  # Almacena ganadores con formato (agency, dni)
        self.lock = threading.Lock()

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        
        signal.signal(signal.SIGTERM, self.__handle_shutdown)

        while True:
            client_sock = self.__accept_new_connection()
            self.__handle_client_connection(client_sock)

    def __handle_shutdown(self, signum, frame):
        """
        Graceful shutdown of the server

        Function that handles SIGTERM signal to gracefully shutdown the server
        """

        logging.info(f'action: shutdown | result: in_progress')
        self._server_socket.close()
        logging.info(f'action: shutdown | result: success')
        exit(0)

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        agency_id = None
        try:
            # Fase 1: Recibir batches de apuestas
            while True: 
                try:
                    bets = decode_bets(client_sock)
                    if not bets:
                        # Mensaje vacío = fin de apuestas
                        break
                    # Guardar agencia del primer bet para después
                    if agency_id is None:
                        agency_id = str(bets[0].agency)
                    store_bets(bets)
                    logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                except ConnectionError:
                    break
            
            # Notificación de fin de apuestas
            send_confirmation(client_sock, True)
            
            # Incrementar contador de agencias completadas
            with self.lock:
                self.agencies_finished_count += 1
                if self.agencies_finished_count == 5:
                    # Ejecutar sorteo
                    self.__perform_lottery()
                    self.sorteo_completed = True
            
            # Fase 2: Esperar consulta de ganadores
            while True:
                try:
                    # Recibir consulta de ganadores
                    query = decode_bets(client_sock)  # Usamos decode_bets pero debería ser vacío
                    
                    # Si sorteo no se completó, esperar
                    if not self.sorteo_completed:
                        send_confirmation(client_sock, False)
                        continue
                    
                    # Obtener ganadores de esta agencia
                    agency_winners = [dni for (agency, dni) in self.winners if agency == int(agency_id)]
                    
                    # Enviar cantidad de ganadores
                    response = str(len(agency_winners))
                    tam_buffer = len(response.encode('utf-8'))
                    header = tam_buffer.to_bytes(2, byteorder='big')
                    sendall(client_sock, header + response.encode('utf-8'))
                    
                    logging.info(f'action: consulta_ganadores | result: success | cantidad: {len(agency_winners)}')
                    break
                    
                except ConnectionError:
                    break
            
        except Exception as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
            try:
                send_confirmation(client_sock, False)
            except:
                pass
        finally:
            client_sock.close()
    
    def __perform_lottery(self):
        """
        Ejecuta el sorteo cargando todas las apuestas y verificando ganadores
        """
        try:
            all_bets = list(load_bets())
            winners = []
            for bet in all_bets:
                if has_won(bet):
                    winners.append((bet.agency, bet.document))
            self.winners = winners
            logging.info(f'action: sorteo | result: success')
        except Exception as e:
            logging.error(f"action: sorteo | result: fail | error: {e}")

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
