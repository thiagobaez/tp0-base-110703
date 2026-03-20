package common

import (
	"fmt"
	"errors"
	"net"
	"os"
	"encoding/csv"
)

const (
	LENGTH_HEADER             = 2
	MAX_MESSAGE_SIZE          = 1024
	MAX_BATCH_SIZE_BYTES      = 8192
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


func loadBetsFromFile(id string) ([]Bet, error) {

	file, err := os.Open("agency.csv")
	if err != nil {
		log.Errorf("action: open_csv_file | result: fail | client_id: %v | error: %v", id, err)
		return []Bet{}, err
	}

	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil {
		log.Errorf("action: read_bets_from_file | result: fail | client_id: %v | error: %v", id, err)
		file.Close()
		return []Bet{}, err
	}

	bets := []Bet{}
	for _, record := range records {
		bet := Bet{
			AgencyId:  id,
			Name:      record[0],
			Lastname:  record[1],
			Dni:       record[2],
			Birthdate: record[3],
			Number:    record[4],
		}
		bets = append(bets, bet)
	}
	file.Close()
	return bets, nil
}


func sendBets(conn net.Conn, bets []Bet, maxBatchAmount int) error {
	i := 0
	for i < len(bets) {
		message := ""
		betsInBatch := 0
		
		for i < len(bets) && betsInBatch < maxBatchAmount {
			bet := bets[i]
			betLine := fmt.Sprintf("%s,%s,%s,%s,%s,%s\n",
				bet.AgencyId,
				bet.Name,
				bet.Lastname,
				bet.Dni,
				bet.Birthdate,
				bet.Number,
			)
			
			if len(message)+len(betLine) > MAX_BATCH_SIZE_BYTES && betsInBatch > 0 {
				break
			}
			
			message += betLine
			betsInBatch++
			i++
		}
		
		if err := sendMessage(conn, message); err != nil {
			return err
		}
	}

	if err := sendMessage(conn, ""); err != nil {
		return err
	}

	return nil
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
