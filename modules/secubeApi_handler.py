#Platzhalter für WEB-Schnittstelle
#Flask oder FastAPI?
import requests
import hashlib
import urllib3

# Warnung unterdrücken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class secubeAPIhandler:

    def __init__(self,
                 api_server='192.168.178.55',
                 api_server_port=8443,
                 api_token="QrOSC1Wq82NrDh8-o3FC0WhSkpz_Qq9Na0uBqSrbcrtL7Ut1Uj-RQVTXI6u1Kmsv5Kt6w-n8At8J1JmcfuCUzw"):
        

        self.api_server = api_server
        self.api_server_port = api_server_port
        self.api_token = api_token
    

    def _sha256sum(self,filepath):
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def download_secube_files(self,api_server,api_port,api_token,filetype="secube_fw",version="latest",download_file_name="file.zip"):
        url = "https://{}:{}/api/v1/download_secube_files".format(api_server,api_port)
        headers = {
                    "Authorization": "Bearer "+api_token,
                    "Content-Type": "application/json"
        }
        data = {
                    "filetype": filetype,
                    "version": version
                }

        response = requests.get(url, headers=headers, json=data, verify=False)
        
        download_data = response.json()

        url = "https://{}:8080{}{}".format(download_data['dl_server'],download_data['path'],download_data['filename'])

        download = requests.get(url, stream=True, verify=False)  # verify=False = SSL ignorieren (nur bei Bedarf)

        if download.status_code == 200:
            with open(download_file_name, "wb") as f:
                for chunk in download.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if (download_data['sha256sum'] == self._sha256sum(download_file_name)):
                print("Download erfolgreich.")
            else:
                print("Download Error - SHA256SUM")
        else:
            print(f"Fehler: {download.status_code} - {download.text}")


    def get_next_command(self,api_server,api_port,api_token):
        url = "https://{}:{}/api/v1/get_cmd".format(api_server,api_port)
        headers = {
                    "Authorization": "Bearer "+api_token,
                    "Content-Type": "application/json"
        }
        commands = requests.get(url, headers=headers, verify=False)
        
        if commands.status_code == 200:
            return commands.json()
        else:
            return None



if __name__ == "__main__":
    secube_api = secubeAPIhandler()
    #secube_api.download_secube_files(api_server=secube_api.api_server,
    #                                 api_port=secube_api.api_server_port,
    #                                 api_token=secube_api.api_token)
    
    commands = secube_api.get_next_command(api_server=secube_api.api_server,api_port=secube_api.api_server_port,api_token=secube_api.api_token)