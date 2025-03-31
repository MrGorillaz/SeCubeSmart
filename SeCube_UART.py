import serial
import time
from tqdm import tqdm

# Konfiguration des Serialports
port = 'COM5'
baudrate = 115200

def xor_sum(hex_values):
    result = 0
    for value in hex_values:
        result ^= value
    return result

def check_xor_sum(xor_summe):
    if(xor_sum(xor_summe) == xor_summe):
        return True
    else:
        return False

def send_command(com_port,com_baud,command,debug=False,get_response=True,response_wait_sec=1.0):
    # Erstellen einer Serial-Instanz
    with serial.Serial(com_port, com_baud, timeout=1) as ser:
        # Die Hex-Daten, die gesendet werden sollen
        xor_summe = xor_sum(command)
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
        


def get_version():
    print("Version Info")
    command = [0x88,0x01,0x00]
    result = list(send_command(port,baudrate,command))
    result_bytes = result[3:-1]
    print("Mode: {}".format(result_bytes[0]))
    print("Software_Version: {}".format(result_bytes[1:2]))
    print("Light Type: {}".format(result_bytes[3]))
    print("\n")

    #Byte 0: Mode: 0 = Bootloader; 1 = User
    #Byte 1-2: software version
    #Byte 3: light type: 0 = standard light; 1 = coloured light


    pass

def calc_results(input_bytes):

    result = 0
    for index,bytes in enumerate(input_bytes):

        result = result+(bytes*256**index)
        pass

    return result


def get_status():
    print("STATUS Info")
    command = [0x88,0x0A,0x00]
    result = list(send_command(port,baudrate,command))
    result_bytes = result[3:-1]
    pass

    print("PIR_Sensor: {}".format(result_bytes[0]))
    print("Cube_Busy: {}".format(result_bytes[1]))
    print("C02_Concentration: {} ppm".format(calc_results(result_bytes[2:6])/100))
    #print("Temperature: {}.{} °C".format(int("".join(f"{x:02x}" for x in result_bytes[6:10]), 16),result_bytes[10]))
    print("Temperature : {} °C".format(calc_results(result_bytes[6:10])/100))
    print("humidity: {} %RH".format(calc_results(result_bytes[10:14])/100))
    print("\n")
#Byte0: pir_sensor
#Byte1: is_cube_busy
#Byte2-5: co2_concentration
#Byte6-9: temperature
#Byte10-13: humidity
#Byte14: not used
#Byte15: not used
#Byte16: not used
#Byte17: fan_selection
#Byte18: is_co2_warning_enabled

def get_date():
    print("Date INFO")
    command = [0x88,0x24,0x00]
    result = list(send_command(port,baudrate,command,get_response=True))
    result_bytes = result[3:-1]

    weekdays = {
                0: "Monday",
                1: "Tuesday",
                2: "Wednesday",
                3: "Thursday",
                4: "Friday",
                5: "Saturday",
                6: "Sunday"
    }


    print("Date: {}, {}.{}.20{}".format(weekdays[result_bytes[6]],result_bytes[2],result_bytes[1],result_bytes[0]))
    print("Time: {}:{}:{}".format(result_bytes[3],result_bytes[4],result_bytes[5]))
    print("\n")
    pass

def test_command(command):
    result = list(send_command(port,baudrate,command,debug=True))
    pass

def set_led_level(level):
    print("Set LED LEVEL:",level)
    command = [0x88,0x1B,0x01,level]
    send_command(port,baudrate,command,debug=True,get_response=False)
    #result_bytes = result[3:-1]

def disable_led():
    print("Disable LED")
    set_led_level(0)
    #command = [0x88,0x1C,0x00]
    #send_command(port,baudrate,command,debug=True,get_response=True)

def set_fan_level(level):
    print("Set FAN LEVEL:",level)
    command = [0x88,0x1D,0x01,level]
    send_command(port,baudrate,command,debug=True,get_response=False)

def disable_fan():
    print("Disable_Fan")
    command = [0x88,0x1E,0x00]
    send_command(port,baudrate,command,debug=True,get_response=False)

#Read_Firmware from Flash
def read_flash(blocks_to_read):
    print("\nReading Flash...")
    read_bytes = [0x88,0x04,0x05]
    start_address = [0x00,0xA0,0x01,0x08]
    read_data = 0x10
    start_adress_int = int.from_bytes(start_address,byteorder='little')
    command= []
    full_firmware_dump = []



    #command = read_bytes
    for block in tqdm(range(blocks_to_read)):
        command = []
        next_address = list((start_adress_int+(block*128)).to_bytes(4,byteorder='little'))
        command.extend(read_bytes)
        command.extend(next_address)
        command.append(read_data)
        firmware_dump = send_command(port,baudrate,command,debug=False,get_response=True,response_wait_sec=0.1)
        full_firmware_dump.append(list(firmware_dump[3:-1]))
    
    return full_firmware_dump

def write_firmware_to_flash(firmware_bytes):
    write_command = [0x88,0x03,0x89,0xBB,0xDD,0xAA,0xCC]
    start_address = [0x00,0xA0,0x01,0x08]
    start_adress_int = int.from_bytes(start_address,byteorder='little')
    number_of_data = [0x10]

    print("\nWriting_firmware...")
    for inc_addr,block in enumerate(tqdm(firmware_bytes)):
        command = []
        next_address = list((start_adress_int+(inc_addr*128)).to_bytes(4,byteorder='little'))
        command.extend(write_command)
        command.extend(next_address)
        command.extend(number_of_data)
        command.extend(block)
        send_command(port,baudrate,command,debug=False,get_response=True,response_wait_sec=0.05)


def erase_flash():
    erase_blocks = []
    delete_command = [0x88,0x02,0x06,0xBB,0xDD,0xAA,0xCC]
    start_erase_address = [0x40,0x03]
    end_erase_address = [0xFF,0x05]
    start_erase_int = int.from_bytes(start_erase_address,byteorder='little')
    end_erase_int = int.from_bytes(end_erase_address,byteorder='little')
    diff_bytes = end_erase_int-start_erase_int
    print("\nErasing Flash...")
    for inc_byte in tqdm(range(diff_bytes+1)):
        command = []
        next_address = list((start_erase_int+inc_byte).to_bytes(2,byteorder='little'))
        command.extend(delete_command)
        command.extend(next_address)
        #print("command: ",list(map(hex,command)))
        send_command(port,baudrate,command,debug=False,get_response=True,response_wait_sec=0.05)
        #erase_blocks.append(next_address)

    pass

#to_do
def read_param():
    print("read param")
    command = [0x88,0x14,0x00]
    send_command(port,baudrate,command,debug=True,get_response=True)


#Read Firmware from File
def read_firmware_file(fw='Sedus_Cube_Steuerung_V83.hex',data_only=False):
    raw_data = open(fw,'r')
    firmware = []
    firmware_data = []

    for raw_line in raw_data:
        raw_line = raw_line.strip()
        start_code = raw_line[0]
        byte_count = int(raw_line[1:3],16)
        adress = raw_line[3:7]
        record_type = int(raw_line[7:9],16)
        check_sum = raw_line[-2:]
        data = raw_line[9:-2]
        data_set = {
                    "startcode":start_code,
                    "bytecount":byte_count,
                    "adress":adress,
                    "recordtype":record_type,
                    "data":data,
                    "checksum":check_sum
        }

        if (data_only and (record_type == 0)):
            firmware_data.append(data_set)
        else:
            firmware.append(data_set)

    if (data_only):
        return firmware_data
    else:
        return firmware


#to_do
def boot_init():
    print("boot_init")
    command = [0x88,0x05,0x04,0xCC,0xAA,0xDD,0xBB]
    send_command(port,baudrate,command,debug=True,get_response=True)



def get_bytes_to_flash2(fw_file='Sedus_Cube_Steuerung_V83.hex'):
    firmware = read_firmware_file(fw=fw_file,data_only=True)
    byte_counter = 0
    firmware_flash_counter = 0
    firmware_to_flash = [[]]
    firmware_stream = []

    for line in firmware:
        firmware_stream.extend(list(bytearray.fromhex(line['data'])))
    
    
    for byte in firmware_stream:

        if len(firmware_to_flash[firmware_flash_counter]) < 128:
            firmware_to_flash[firmware_flash_counter].append(byte)
            byte_counter = byte_counter+1
        else:
            byte_counter = 0
            firmware_flash_counter = firmware_flash_counter+1
            firmware_to_flash.append([])
            firmware_to_flash[firmware_flash_counter].append(byte)

        
    if len(firmware_to_flash[-1]) < 128:
        firmware_to_flash[-1].extend(bytearray.fromhex('00'*(128-len(firmware_to_flash[-1]))))
    
    #filup
    firmware_to_flash.append(list(bytearray.fromhex('00'*128)))
    return firmware_to_flash

        
        

#To_DO
#Es gibt einen Overflow, da zwischenzeitig weniger Bytes reinkommen.
#Am besten ist es einzelne Bytes zu laden, bis eine Länge von 128 erreicht ist.
#GGF. am Ende mit 0x00 auffüllen
def get_bytes_to_flash():

    firmware = read_firmware_file(data_only=True)
    byte_counter = 0
    firmware_flash_counter = 0
    firmware_to_flash = [[]]
    

    for block,line in enumerate(firmware):

        if firmware_flash_counter == 530:
            print("stop")


        if (byte_counter < 128):
            firmware_to_flash[firmware_flash_counter].extend(list(bytearray.fromhex(firmware[block]['data'])))
            byte_counter = len(firmware_to_flash[firmware_flash_counter])
        else:
            byte_counter = 0
            firmware_flash_counter = firmware_flash_counter+1
            firmware_to_flash.append([])
            firmware_to_flash[firmware_flash_counter].extend(list(bytearray.fromhex(firmware[block]['data'])))
    
    if (len(firmware_to_flash[-1]) < 128):


        firmware_to_flash[-1].extend(bytearray.fromhex('00'*(128-len(firmware_to_flash[-1]))))
        
        if (len(firmware_to_flash[-1]) != 128):
            print("oho")
            pass
    
    #filup
    firmware_to_flash.append(list(bytearray.fromhex('00'*128)))
    return firmware_to_flash


def verify_flash(firmware_data_file,firmware_data_flash):

    if (len(firmware_data_file) == len(firmware_data_flash)):
        print("Phase 1: Length Check OK!")
    else:
        print("Error: Length doesnt match!!!")
        return
    

    hash_check = True
    for i in tqdm(range(len(firmware_data_file))):
            
            if (len(firmware_data_file[i]) == len(firmware_data_flash[i])):
                
                for index,data in enumerate(firmware_data_file[i]):
                    
                    if data == firmware_data_flash[i][index]:
                        pass
                    else:
                        print("Error an Block:",i)
                        return False

            else:
                 print("Error an Block:",i)
                 return False

    print("Phase 2: Ok")
    return True





def write_new_app_flag():
    print("write new app Flag....",end='')
    command = [0x88,0x07,0x04,0xBB,0xDD,0xAA,0xCC]
    resp = send_command(port,baudrate,command,debug=False,get_response=True,response_wait_sec=1.0)
    if (type(resp) == bytes):
        print("OK!")
    else:
        print("Error - Flag not Set!!!")

def restart_controller():
    print("Restarting...",end='')
    command = [0x88,0x06,0x04,0xBB,0xDD,0xAA,0xCC]
    resp = send_command(port,baudrate,command,debug=False,get_response=True,response_wait_sec=1.0)
    print("OK!")
  





#firmware_raw = read_firmware_file(data_only=True)
#get_version()
#firmware_data = get_bytes_to_flash()
#firmware_data = get_bytes_to_flash2(fw_file='Sedus_Cube_Steuerung_V80.hex')
#
#get_version()
#erase_flash()
#time.sleep(1.0)
#write_firmware_to_flash(firmware_bytes=firmware_data)
#print('\nVerifying Firmware...')
#firmware_flash = read_flash(blocks_to_read=len(firmware_data))
#successful_flash = verify_flash(firmware_data,firmware_flash)
#
#if (successful_flash):
#    write_new_app_flag()
#    time.sleep(1)
#    restart_controller()
#
#time.sleep(10.0)
#get_version()
#write_firmware_to_flash(firmware_bytes=firmware_data)

#get_version()
#get_status()
#get_date()
#disable_led()
#read_flash()
#set_led_level(100)
#time.sleep(1.0)
#boot_init()
#read_param()

#for i in range(25,100):
#    set_fan_level(40)
#    time.sleep(0.5)
#    set_fan_level(50)
#    time.sleep(0.05)

#disable_fan()

#for i in range (10):
#    time.sleep(1.0)
#    get_status()
for i in range(10):
    #get_status()
    for level in range(1,55,2):
        set_led_level(level)
        time.sleep(0.05)

#    for level in  reversed(range(1,55,2)):
#        set_led_level(level)
#        time.sleep(0.05)
#    #test_command([0x88,0x25,0x01,0x01])
#disable_led()
#