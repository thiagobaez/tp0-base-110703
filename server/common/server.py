import socket
import logging
import signal
import threading
import time
from .utils import Bet, decode_bets, store_bets, send_confirmation, load_bets, has_won, send_winners, receive_query

class Server:
    def __init__(self, port, listen_backlog, num_clients):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        
        self.winners = []
        self.num_clients = num_clients
        
        self.lock = threading.Lock()
        self.agencies_finished_count = 0
        self.sorteo_completed = False
        self.phase_1_done = threading.Condition(self.lock)
        
        self._shutdown_event = threading.Event()
        self._active_threads = []

    def run(self):
        """
        Server loop that accepts connections in parallel and processes them in threads
        """
        signal.signal(signal.SIGTERM, self.__handle_shutdown)
        
        client_count = 0
        
        try:
            # FASE 1: Aceptar y procesar todas las apuestas
            while client_count < self.num_clients and not self._shutdown_event.is_set():
                client_sock = self.__accept_new_connection()
                
                client_thread = threading.Thread(
                    target=self.__handle_client_connection,
                    args=(client_sock,),
                    daemon=False
                )
                self._active_threads.append(client_thread)
                client_thread.start()
                client_count += 1
            
            # Esperar a que todos los clients terminen de enviar apuestas
            with self.phase_1_done:
                while self.agencies_finished_count < self.num_clients:
                    self.phase_1_done.wait()
            
            logging.info('action: phase_1_complete | result: success')
            
            # FASE 2: Ejecutar lotería
            self.__perform_lottery()
            
            # Notificar que el sorteo está completado
            with self.lock:
                self.sorteo_completed = True
            
            # FASE 3: Aceptar nuevas conexiones para consultas de ganadores
            logging.info('action: phase_2_start | result: in_progress')
            query_count = 0
            
            while query_count < self.num_clients and not self._shutdown_event.is_set():
                client_sock = self.__accept_new_connection()
                
                client_thread = threading.Thread(
                    target=self.__handle_client_query,
                    args=(client_sock,),
                    daemon=False
                )
                self._active_threads.append(client_thread)
                client_thread.start()
                query_count += 1
            
            # Esperar a que todos los threads terminen
            for thread in self._active_threads:
                thread.join(timeout=10)
                
            logging.info('action: all_clients_done | result: success')
            
        except Exception as e:
            logging.error(f"action: run | result: fail | error: {e}")
        finally:
            self._shutdown_event.set()

    def __handle_shutdown(self, signum, frame):
        """
        Graceful shutdown of the server in multithreading environment
        
        Closes the server socket and signals shutdown event
        """
        logging.info(f'action: shutdown | result: in_progress')
        self._shutdown_event.set()
        try:
            self._server_socket.close()
        except:
            pass
        logging.info(f'action: shutdown | result: success')
        exit(0)

    def __handle_client_query(self, client_sock):
        """
        Procesa queries de ganadores en Fase 2
        
        Recibe query con agency_id y envía winners
        """
        try:
            is_winner_query, agency_id = receive_query(client_sock)
            
            if is_winner_query and agency_id:
                agency_winners = [dni for (agency, dni) in self.winners if agency == agency_id]
                send_winners(client_sock, agency_winners)
                logging.info(f'action: consulta_ganadores | result: success | cant_ganadores: {len(agency_winners)}')
        except Exception as e:
            logging.error(f"action: handle_query | result: fail | error: {e}")
        finally:
            client_sock.close()
    
    def __handle_client_connection(self, client_sock):
        """
        Procesa apuestas de un cliente en Fase 1
        """
        agency_id = None
        try:
            # FASE 1: Recibir apuestas
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
            
            # Notificar que se completó Fase 1
            with self.phase_1_done:
                self.agencies_finished_count += 1
                if self.agencies_finished_count == self.num_clients:
                    logging.info('action: all_agencies_bets_received | result: success')
                self.phase_1_done.notify_all()
            
        except Exception as e:
            logging.error(f"action: handle_client | result: fail | error: {e}")
            try:
                send_confirmation(client_sock, False)
            except:
                pass
        finally:
            client_sock.close()
    
    def __perform_lottery(self):

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

     
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c