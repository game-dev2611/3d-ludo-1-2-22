import socket
from ursina.vec3 import Vec3
import json
class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server =socket.gethostbyname(socket.gethostname())
        self.port = 2611
        self.addr = (self.server,self.port)
        self.pos =self.connect()
        self.loads, self.dumps = lambda b: json.loads(b.decode()), lambda o: json.dumps(o).encode()

    def getPos(self):
        return self.pos
    def connect(self):
        try:
            self.client.connect(self.addr)
            print("try")
            return self.loads(self.client.recv(2048))

        except socket.error as e:
            print(e)
    def send(self, data):
        try:
            self.client.send(data)
            return self.loads(self.client.recv(2048))
        except socket.error as e:
            print(e)
