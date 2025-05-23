import modules.secubeDriver as driver
import modules.secubeApi_handler as api
import modules.secube_mqtt_handler as mqtt
import time
import zipfile
import os

cube = driver.secubeDriver(debug=False,port='/dev/ttyAMA5')
cube_api = api.secubeAPIhandler()
cube_mqtt = mqtt.secubeMQTT()

def do_cmd(cmd):
    
    if (cmd["cmd"] == 'test-light'):
        cube.set_light_level_test(cmd["value"])
        return True
    
    if (cmd['cmd'] == 'test-fan'):
        cube.set_fan_level_test(cmd["value"])
        return True
    
    if (cmd['cmd'] == 'test-led'):
        cube.set_led_level_test(cmd["value"])
        return True
    
    if (cmd['cmd'] == 'disable-light'):
        cube.set_light_level_test(0)
        return True
    
    if (cmd['cmd'] == 'disable-led'):
        cube.disable_led()
        return True
    
    if (cmd['cmd'] == 'disable-fan'):
        cube.disable_fan()
        return True
    
    return False



def is_time_up(end_time):

    if (time.time() >= end_time):
        return True
    else:
        return False
    

next_cycle = time.time()

serial = cube.get_serialNumber()
identity = "secube/{}".format(serial)
    
while (True):

    #version = cube.get_version()
    ''
    status = cube.get_status()
    
    cube_mqtt.send_mqtt_data(data = status,top_topic=identity)





    commands = cube_api.get_next_command(cube_api.api_server,cube_api.api_server_port,cube_api.api_token)

    #print(commands)

    if len(commands["next_commands"]) > 0:
        for command in commands['next_commands']:
            print(command)
            do_cmd(command)

#cube_api.download_secube_files(cube_api.api_server,cube_api.api_server_port,cube_api.api_token,version='v83')

# Pfad zur ZIP-Datei
#zip_pfad = 'file.zip'

# Zielverzeichnis
#ziel_verzeichnis = 'secube_fw'

# ZIP-Datei öffnen und extrahieren
#with zipfile.ZipFile(zip_pfad, 'r') as zip_ref:
#    zip_ref.extractall(ziel_verzeichnis)

#print(f'Dateien wurden in "{ziel_verzeichnis}" extrahiert.')

#cube.update_firmware(file='/home/secube/secube_fw/v83.hex')
#cube.set_led_level(60)
#cube.set_led_level(30)