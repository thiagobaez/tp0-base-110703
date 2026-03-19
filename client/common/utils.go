package common

import (
	"fmt"
	"errors"
	"net"
)

const (
	LENGTH_HEADER             = 2
	MAX_MESSAGE_SIZE          = 1024
	IDX_MESSAGE_CONFIRMATION  = 0x01
	IDX_CONFIRMATION_SUCCESS  = 0x01
	IDX_CONFIRMATION_FAIL     = 0x00
)


type Bet struct {
	AgencyId  string
	Name      string
	Lastname  string
	Dni       string
	Birthdate string
	Number    string
}

func sendall(conn net.Conn, buffer []byte) error {

	totalSent := 0
	for totalSent < len(buffer) {
		n, err := conn.Write(buffer[totalSent:])
		if err != nil {
			return err
		}
		totalSent += n
	}
	return nil
}

func recvall(conn net.Conn, n int) ([]byte, error) {

	buffer := make([]byte, n)
	totalRead := 0
	for totalRead < n {
		readBytes, err := conn.Read(buffer[totalRead:])
		if err != nil {
			return nil, err
		}
		totalRead += readBytes
	}
	return buffer, nil
}


func sendMessage(conn net.Conn, message string) error {

	buffer := []byte(message)
	
	if len(buffer) > MAX_MESSAGE_SIZE {
		return errors.New("message too long")
	}
	
	tamanio_mensaje := uint16(len(buffer))
	header := make([]byte, LENGTH_HEADER)

	header[0] = byte(tamanio_mensaje >> 8)
	header[1] = byte(tamanio_mensaje & 0xFF)

	if err := sendall(conn, header); err != nil {
		return err
	}

	if err := sendall(conn, buffer); err != nil {
		return err
	}

	return nil

}


func sendBet(conn net.Conn, bet Bet) error {

	message := fmt.Sprintf("%s,%s,%s,%s,%s,%s",
	 bet.AgencyId, 
	 bet.Name, 
	 bet.Lastname, 
	 bet.Dni, 
	 bet.Birthdate, 
	 bet.Number)


	return sendMessage(conn, message)
}

func receiveMessage(conn net.Conn) (bool, error) {

	response, err := recvall(conn, LENGTH_HEADER)
	if err != nil {
		return false, err
	}

	if response[0] == IDX_MESSAGE_CONFIRMATION {
		if response[1] == IDX_CONFIRMATION_SUCCESS {
			return true, nil
		} else if response[1] == IDX_CONFIRMATION_FAIL {
			return false, nil
		}
	}

	return false, errors.New("invalid response")
}
