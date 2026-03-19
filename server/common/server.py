import socket
import logging
import signal
from .utils import Bet, decode_bet, store_bets, send_confirmation
class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

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
        try:
            bet = decode_bet(client_sock)
            addr = client_sock.getpeername()
            logging.info(f'action: received_bet | result: success | ip: {addr[0]}')
            store_bets([bet])
            logging.info(f'action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}')
            send_confirmation(client_sock, True)

        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
            send_confirmation(client_sock, False)
        finally:
            client_sock.close()

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
