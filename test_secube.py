import modules.secubeDriver as driver
import modules.secubeApi_handler as api
import zipfile
import os

cube = driver.secubeDriver(debug=False,port='/dev/ttyAMA5')
cube_api = api.secubeAPIhandler()
cube.get_version()
''
cube.get_status()

commands = cube_api.get_next_command(cube_api.api_server,cube_api.api_server_port,cube_api.api_token)

print(commands)

cube_api.download_secube_files(cube_api.api_server,cube_api.api_server_port,cube_api.api_token,version='v83')

# Pfad zur ZIP-Datei
zip_pfad = 'file.zip'

# Zielverzeichnis
ziel_verzeichnis = 'secube_fw'

# ZIP-Datei öffnen und extrahieren
with zipfile.ZipFile(zip_pfad, 'r') as zip_ref:
    zip_ref.extractall(ziel_verzeichnis)

print(f'Dateien wurden in "{ziel_verzeichnis}" extrahiert.')

#cube.update_firmware(file='/home/secube/secube_fw/v83.hex')
#cube.set_led_level(60)
#cube.set_led_level(30)