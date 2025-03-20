import serial
import time
from tqdm import tqdm

class secubeDriver:

    #Konstruktor
    def __init__(self):

        self.port = 'COM5'
        self.baudrate = 115200

    #Berechnung der Checksumme
    def __xor_sum(self.hex_values):
        result = 0
        for value in hex_values:
            result ^= value
        return result

    #Prüfen der Checksummen
    def __check_xor_sum(self,xor_summe):
        if(__xor_sum(xor_summe) == xor_summe):
            return True
        else:
            return False
    

    #Senden der Seriellen Befehle
    def send_command(self,com_port,com_baud,command,debug=False,get_response=True,response_wait_sec=1.0):
        
        # Erstellen einer Serial-Instanz
        with serial.Serial(com_port, com_baud, timeout=1) as ser:
            # Die Hex-Daten, die gesendet werden sollen
            xor_summe = __xor_sum(command)
            command.append(xor_summe)
            #data_to_send = bytes([0x88, 0x10,0x00, 0x90])
            data_to_send = bytes(command)

            # Sende die Daten
            ser.write(data_to_send)
            if debug:
                print(f'Daten gesendet: {data_to_send.hex()}')

            # Warte auf eine Antwort
            if get_response:
                time.sleep(response_wait_sec)  # Optional: Warten, um sicherzustellen, dass die Antwort kommt
                response = ser.read(ser.in_waiting or 1)  # Lese die Antwort, wenn sie verfügbar ist

                # Antwort anzeigen
                if response:
                    if debug:
                        print(f'Antwort empfangen: {response.hex()}')
                        ser.close()
                    return response
                else:
                    if debug:
                        print('Keine Antwort empfangen.')
                        ser.close()
                    return 0
            else:
                ser.close()
                return 0
    



    