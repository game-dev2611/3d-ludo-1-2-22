import socket
from _thread import *
from ursina import Vec3
import json
server = socket.gethostbyname(socket.gethostname())
port = 2611
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind((server, port))
except socket.error as e:
    print(str(e))
s.listen(2)
class NamedObject:
    def __init__(self,name,value):
        self.name = name
        self.value = value



print("waiting for a connection, server started")
VEC_NUM = [[[2, 2], [4, 2], [2, 4], [4, 4]],
                        [[15 - 2, 2], [15 - 4, 2], [15 - 2, 4], [15 - 4, 4]],
                        [[2, 15 - 2], [4, 15 - 2], [2, 15 - 4], [4, 15 - 4]],
                        [[15 - 2, 15 - 2], [15 - 4, 15 - 2], [15 - 2, 15 - 4], [15 - 4, 15 - 4]]]
token_pos = [[], [], [], []]
for i in range(len(VEC_NUM)):
    li1 = VEC_NUM[i]
    li2 = token_pos[i]
    for j in range(len(VEC_NUM)):
        vecobj = li1[j]
        li2.append(Vec3(vecobj[0] * 4, 4, vecobj[1] * 4))

loads,dumps = lambda b:json.loads(b.decode()),lambda o:json.dumps(o).encode()

def read_pos(string):
    return Vec3(*(int(val) for val in string.split(",")[:]))
def make_pos(vec3: Vec3):
    return str(vec3)
def threaded_client(conn,player):
    conn.send(loads(NamedObject(name="pos",value=token_pos[0][player])))
    reply = ""
    while True:
        try:
            data = make_pos(conn.recv(2048).decode("utf-8"))
            token_pos[player] = data
            if not data:
                print("Disconnected")
                break
            else:
                if player == 0:
                    reply = token_pos[0]
                else:
                    reply = token_pos[1]
            conn.sendAll(reply)
        except:
            break
    print("Disconnected")
    conn.close()
currentPlayer = 0
while True:
    conn, addr = s.accept()
    print("connected to ",addr)
    start_new_thread(threaded_client,(conn,currentPlayer))
    currentPlayer+=1
