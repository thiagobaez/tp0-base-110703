package common

import (

	"net"
	"time"
	"os"
	"os/signal"
	"syscall"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	bet    Bet
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig, bet Bet) *Client {
	client := &Client{
		config: config,
		bet: bet,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGTERM)

	// Flag para cortar ejecución
	running := true

	// Goroutine que escucha SIGTERM
	go func() {
		<-sigs
		log.Infof("action: sigterm_received | result: success | client_id: %v", c.config.ID)
		running = false

		if c.conn != nil {
			c.conn.Close()
		}
	}()
	
	if err := c.createClientSocket(); err != nil {
		log.Criticalf(
			"action: create_client_socket | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		os.Exit(1)
	}

	if err := sendBet(c.conn, c.bet); err != nil {
		log.Criticalf(
			"action: send_bet | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		os.Exit(1)
	} else {
		log.Infof(
			"action: apuesta_enviada | result: success | dni: %s | numero: %s",
			c.bet.Dni,
			c.bet.Number,
		)
	}

	confirmation, err := receiveMessage(c.conn)
	if err != nil {
		log.Criticalf(
			"action: receive_confirmation | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		os.Exit(1)
	}

	if confirmation {
		log.Infof(
			"action: bet_confirmation | result: success | client_id: %v",
			c.config.ID,
		)
	} else {
		log.Infof(
			"action: bet_confirmation | result: fail | client_id: %v",
			c.config.ID,
		)
	}

	c.conn.Close()

}
