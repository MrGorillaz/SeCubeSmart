from  paho.mqtt import client as mqtt
import random

class secubeMQTT:

    def __init__(self,mqtt_server='192.168.178.55',mqtt_port=1883,mqtt_user="sedus",mqtt_pw="sedus123",mqtt_timeout=60):
        self.mqtt_server = mqtt_server
        self.mqtt_port = mqtt_port
        self.mqtt_timeout = mqtt_timeout
        self.mqtt_user = mqtt_user
        self.mqtt_pw = mqtt_pw
        self.mqtt_client = self.__create_client()

    def __create_client(self):
        def on_connect(client, userdata, flags, rc):
        # For paho-mqtt 2.0.0, you need to add the properties parameter.
        # def on_connect(client, userdata, flags, rc, properties):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)
        # Set Connecting Client ID
        client_id = f'python-mqtt-{random.randint(0, 1000)}'
        #client = mqtt.Client()
    
        # For paho-mqtt 2.0.0, you need to set callback_api_version.
        client = mqtt.Client(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    
        # client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.username_pw_set(self.mqtt_user,self.mqtt_pw)
        client.connect(self.mqtt_server,self.mqtt_port,self.mqtt_timeout)
        return client
    
    def send_mqtt_data(self,data,top_topic="secube"):

        if data != None:

            for topic,value in data.items():
                self.mqtt_client.publish("{}/{}".format(top_topic,topic),value)



        


if __name__ == "__main__":

    mqtt_obj = secubeMQTT()
    mqtt_obj.send_mqtt_data("data")
