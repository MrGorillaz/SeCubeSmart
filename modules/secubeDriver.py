import serial
import time
from tqdm import tqdm
import yaml
import os.path
import copy

class secubeDriver:

    #Konstruktor
    def __init__(self,port='/dev/ttyS0',baudrate=115200,cube_version=1,debug=False,response=True,response_time=1.0):

        self.port = port
        self.baudrate = baudrate
        self.cube_version = "secube_v"+str(cube_version)
        self.commands = None
        self.debug = debug
        self.response = response
        self.response_time = response_time
        self.__read_config(self.cube_version)




    #Private Methoden
    def __read_config(self,version):
        base_path = os.path.dirname(os.path.abspath(__file__))  # Ordner der aktuellen Datei
        yaml_path = os.path.join(base_path, "secube_commands.yaml")
        with open(yaml_path, "r") as file:
            config_data = yaml.safe_load(file)
        self.commands = {list(item.keys())[0]: list(item.values())[0] for item in config_data.get(version, {}).get("command", [])}
        

    #Berechnung der Checksumme
    def __xor_sum(self,hex_values):
        result = 0
        for value in hex_values:
            result ^= value
        return result

    #Prüfen der Checksummen
    def __check_xor_sum(self,xor_summe):
        if(self.__xor_sum(xor_summe) == xor_summe):
            return True
        else:
            return False
    
    def __calc_results(self,input_bytes):

        result = 0
        for index,bytes in enumerate(input_bytes):

            result = result+(bytes*256**index)
            pass

        return result

    #Senden der Seriellen Befehle
    def __send_command(self,com_port,com_baud,command,debug=False,get_response=True,response_wait_sec=1.0):

        
        # Erstellen einer Serial-Instanz
        with serial.Serial(com_port, com_baud, timeout=self.response_time) as ser:
            # Die Hex-Daten, die gesendet werden sollen
            xor_summe = self.__xor_sum(command)

            #bugfixing durch deepcopy, weil sonst originales classenobjekt immer verändert wurde
            command = copy.deepcopy(command)
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
            
################## FIRMWARE HANDLING ########################################################
            
    #Read Firmware from File
    def __read_firmware_file(self,fw='Sedus_Cube_Steuerung_V83.hex',data_only=False):
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

    #Read_Firmware from Flash
    def __read_flash(self,blocks_to_read):
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
            firmware_dump = self.__send_command(self.port,self.baudrate,command,debug=False,get_response=True,response_wait_sec=0.1)
            full_firmware_dump.append(list(firmware_dump[3:-1]))

        return full_firmware_dump
    
    def __write_firmware_to_flash(self,firmware_bytes):
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
            self.__send_command(self.port,self.baudrate,command,debug=False,get_response=True,response_wait_sec=0.05)

    def __erase_flash(self):
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
            self.__send_command(self.port,self.baudrate,command,debug=False,get_response=True,response_wait_sec=0.05)
            #erase_blocks.append(next_address)

        pass

    def __get_bytes_to_flash(self,fw_file='Sedus_Cube_Steuerung_V83.hex'):
        firmware = self.__read_firmware_file(fw=fw_file,data_only=True)
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

    def __verify_flash(self,firmware_data_file,firmware_data_flash):

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

    def __write_new_app_flag(self):
        print("write new app Flag....",end='')
        command = [0x88,0x07,0x04,0xBB,0xDD,0xAA,0xCC]
        resp = self.__send_command(self.port,self.baudrate,command,debug=False,get_response=True,response_wait_sec=1.0)
        if (type(resp) == bytes):
            print("OK!")
        else:
            print("Error - Flag not Set!!!")
    
    def __get_param_1(self):
        print("Get Param 1 Values")
        command = self.commands['read_param_1']
        result = list(self.__send_command(self.port,self.baudrate,command,debug=self.debug,get_response=self.response))
        return result

    def __get_param_2(self):
        print("Get Param 2 Values")
        command = self.commands['read_param_2']
        result = list(self.__send_command(self.port,self.baudrate,command,debug=self.debug,get_response=self.response))
        return result
    
    def __write_param_1(self,params):
        print('Writing Param 1')
        command = self.commands['write_param_1']
        command = copy.deepcopy(command)
        command.extend(params)
        self.__send_command(self.port,self.baudrate,command,debug=self.debug,get_response=self.response,response_wait_sec=1.2)
        pass

        

    
###################################################################################################################
    #Öffentliche Methoden

    def get_serialNumber(self):
        
        resp = self.__get_param_1()
        SN_part = map(chr,resp[171:177])
        SerialNumber = ''.join(SN_part)
        print('SerialNumber: {}'.format(SerialNumber))

    
    def set_serialNumber(self,new_serial='FH-SWF'):
        resp = self.__get_param_1()

        resp[171:177] = list(new_serial.encode('utf-8'))

        new_params = resp[3:-1]
        self.__write_param_1(params=new_params)
        pass

    def get_param1(self):
        resp = self.__get_param_1()
        pass


    def get_params2(self):
        resp = self.__get_param_2()
        pass 
    
    def get_version(self):
        print("Version Info")
        #command = [0x88,0x01,0x00]
        command = self.commands['info']
        result = list(self.__send_command(self.port,self.baudrate,command,debug=self.debug,get_response=self.response))
        result_bytes = result[3:-1]
        print("Mode: {}".format(result_bytes[0]))
        print("Software_Version: {}".format(result_bytes[1:2]))
        print("Light Type: {}".format(result_bytes[3]))
        print("\n")

    #Byte 0: Mode: 0 = Bootloader; 1 = User
    #Byte 1-2: software version
    #Byte 3: light type: 0 = standard light; 1 = coloured light

    def get_status(self):
        print("STATUS Info")
        #command = [0x88,0x0A,0x00]
        command = self.commands['status']
        result = list(self.__send_command(self.port,self.baudrate,command,debug=self.debug,get_response=True))
        result_bytes = result[3:-1]
        pass

        print("PIR_Sensor: {}".format(result_bytes[0]))
        print("Cube_Busy: {}".format(result_bytes[1]))
        print("C02_Concentration: {} ppm".format(self.__calc_results(result_bytes[2:6])/100))
        #print("Temperature: {}.{} °C".format(int("".join(f"{x:02x}" for x in result_bytes[6:10]), 16),result_bytes[10]))
        print("Temperature : {} °C".format(self.__calc_results(result_bytes[6:10])/100))
        print("humidity: {} %RH".format(self.__calc_results(result_bytes[10:14])/100))
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

    def set_led_level_test(self,level):
        print("Set LED LEVEL TEST:",level)
        #command = [0x88,0x1B,0x01,level]
        command = self.commands['led']
        command.append(level)
        self.__send_command(self.port,self.baudrate,command,debug=self.debug,get_response=self.response)
        #result_bytes = result[3:-1]

    def disable_led(self):
        print("Disable LED")
        #self.set_led_level(0)
        #command = [0x88,0x1C,0x00]
        command = self.commands['disable_led']
        self.__send_command(self.port,self.baudrate,command,debug=self.debug,get_response=self.response)

    def set_fan_level_test(self,level):
        print("Set FAN LEVEL TEST:",level)
        #command = [0x88,0x1D,0x01,level]
        command = self.commands['fan']
        command.append(level)
        self.__send_command(self.port,self.baudrate,command,debug=self.debug,get_response=self.response)

    def disable_fan(self):
        print("Disable_Fan")
        #command = [0x88,0x1E,0x00]
        command = self.commands['disable_fan']
        self.__send_command(self.port,self.baudrate,command,debug=self.debug,get_response=self.response)
    
    def set_light_level_test(self,level=10,colour=10):
        print("SET LIGHT LEVEL TEST:",level)
        command = self.commands['light']
        command.extend([level,colour,colour])
        self.__send_command(self.port,self.baudrate,command,debug=self.debug,get_response=self.response,response_wait_sec=1.2)
    


    def set_light_start(self,level):
        print("SET LIGHT LEVEL:",level)
        resp = self.__get_param_1()
        resp[51] = level
        new_params = resp[3:-1]
        self.__write_param_1(params=new_params)
        pass

    
    def get_display_params(self,group=1):
        print("GET DISPLAY INFO-Group:",group)
        command = self.commands['read_display_param']
        command.append(group)
        result = list(self.__send_command(self.port,self.baudrate,command,debug=self.debug,get_response=self.response))
        pass

    def get_display_data(self):
        print("GET DISPLAY INFO")
        command = self.commands['read_display_data']
        result = list(self.__send_command(self.port,self.baudrate,command,debug=self.debug,get_response=self.response))
        pass
        
        

    def get_date(self):
        print("Date INFO")
        #command = [0x88,0x24,0x00]
        command = self.commands['date']
        result = list(self.__send_command(self.port,self.baudrate,command,debug=self.debug,get_response=self.response))
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


        print("Date: {}, {:02d}.{:02d}.20{}".format(weekdays[result_bytes[6]],result_bytes[2],result_bytes[1],result_bytes[0]))
        print("Time: {:02d}:{:02d}:{:02d}".format(result_bytes[3],result_bytes[4],result_bytes[5]))
        print("\n")
        pass

    def restart_controller(self):
        print("Restarting...",end='')
        #command = [0x88,0x06,0x04,0xBB,0xDD,0xAA,0xCC]
        command = self.commands['restart']
        resp = self.__send_command(self.port,self.baudrate,command,debug=False,get_response=True,response_wait_sec=1.0)
        print("OK!")

    def update_firmware(self,file='Sedus_Cube_Steuerung_V80.hex'):

        firmware_data = self.__get_bytes_to_flash(fw_file=file)
        self.__erase_flash()
        time.sleep(1.0)
        self.__write_firmware_to_flash(firmware_bytes=firmware_data)
        print('\nVerifying Firmware...')
        firmware_flash = self.__read_flash(blocks_to_read=len(firmware_data))
        successful_flash = self.__verify_flash(firmware_data,firmware_flash)

        if (successful_flash):
            self.__write_new_app_flag()
            time.sleep(1)
            self.restart_controller()
            time.sleep(10.0)
        else:
            print("Flashing Firmware - Failed")



##### Testing #################

if __name__ == "__main__":
    print ("hello")

    cube = secubeDriver(debug=False,port='/dev/ttyAMA5',baudrate=115200,response_time=1.0)
    #cube.restart_controller()
    cube.set_led_level_test(level=30)
    cube.set_fan_level_test(30)
    #cube.get_status()
    #cube.get_version()
    #cube.get_serialNumber()
    #cube.set_serialNumber(new_serial='FH-SWF')
    #cube.get_serialNumber()
    #cube.get_params2()
    cube.set_light_level_test(50,100)
  
  
    #cube.disable_led()
    #cube.get_date()
    #cube.set_fan_level(100)
    #time.sleep(10.0)
    #cube.set_fan_level(30)
    #cube.set_led_level(80)
    #cube.get_date()
    #cube.update_firmware(file='/home/secube/SeCubeSmart/Sedus_Cube_Steuerung_V73.hex')
    #cube.restart_controller()




    