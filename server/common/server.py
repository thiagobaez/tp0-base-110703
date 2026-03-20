import socket
import logging
import signal
from .utils import Bet, decode_bets, store_bets, send_confirmation
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
            total_bets = 0
            while True: 
                try:
                    bets = decode_bets(client_sock)
                    if not bets:
                        break
                    store_bets(bets)
                    logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                    total_bets += len(bets)
                except ConnectionError:
                    break
            send_confirmation(client_sock, True)
        except Exception as e:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {len(bets)}")
            try:
                send_confirmation(client_sock, False)
            except:
                pass
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
