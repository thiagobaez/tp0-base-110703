import socket
import logging
import signal
from .utils import Bet, decode_bets, store_bets, send_confirmation, load_bets, has_won, send_winners, receive_query


class Server:
    def __init__(self, port, listen_backlog, num_clients):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.winners = []  
        self.num_clients = num_clients

    def run(self):
        
        signal.signal(signal.SIGTERM, self.__handle_shutdown)

        for _ in range(self.num_clients):
            client_sock = self.__accept_new_connection()
            self.__handle_bets(client_sock)
        
        self.__perform_lottery()
        
        for _ in range(self.num_clients):
            client_sock = self.__accept_new_connection()
            self.__handle_query(client_sock)

    def __handle_shutdown(self, signum, frame):
        """
        Graceful shutdown of the server

        Function that handles SIGTERM signal to gracefully shutdown the server
        """

        logging.info(f'action: shutdown | result: in_progress')
        self._server_socket.close()
        logging.info(f'action: shutdown | result: success')
        exit(0)

    def __handle_bets(self, client_sock):
        agency_id = None
        try:
            while True: 
                try:
                    bets = decode_bets(client_sock)
                    if not bets:
                        break
                    if agency_id is None:
                        agency_id = str(bets[0].agency)
                    store_bets(bets)
                    logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
                except ConnectionError:
                    break
            
            send_confirmation(client_sock, True)
            logging.info(f'action: apuestas_confirmadas | result: success | agency_id: {agency_id}')
            
        except Exception as e:
            logging.error(f"action: receive_bets | result: fail | error: {e}")
            try:
                send_confirmation(client_sock, False)
            except:
                pass
        finally:
            client_sock.close()
    
    def __handle_query(self, client_sock):
        """
        Fase 3: Recibe query de ganadores de un cliente y envía resultado
        """
        try:
            is_winner_query, agency_id = receive_query(client_sock)
            
            if is_winner_query:
                # El sorteo ya está completado en esta fase
                agency_winners = [dni for (agency, dni) in self.winners if agency == agency_id]
                send_winners(client_sock, agency_winners)
                logging.info(f'action: respuesta_ganadores | result: success | agency_id: {agency_id} | cant_ganadores: {len(agency_winners)}')
            
        except Exception as e:
            logging.error(f"action: receive_query | result: fail | error: {e}")
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
