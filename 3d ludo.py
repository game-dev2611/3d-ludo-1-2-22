#import numpy as np
#from PIL import ImageGrab
#import schedule
#import plyer
from email.errors import FirstHeaderLineIsContinuationDefect
from perlin_noise import PerlinNoise
import pyttsx3
from functools import update_wrapper
from json.decoder import JSONDecodeError
from math import *
from tkinter import *
from tkinter.ttk import *
from numpy import Inf, rot90
from enum import Enum
from ursina.scripts.combine import combine
from ursina.shaders.basic_lighting_shader import basic_lighting_shader
from ursina.shaders.texture_blend_shader import texture_blend_shader
from ursina.ursinamath import distance_xz
from time import timezone
from ursina import shaders, vec2
from ursina.prefabs.health_bar import HealthBar
import json
import json
import psutil
#from network import Network
from ursina import *
from ursina import curve
from ursina.lights import DirectionalLight
from ursina.prefabs.first_person_controller import FirstPersonController
import inspect

b = psutil.sensors_battery().percent
window.title = "3d Ludo"
window.borderless = False

class Program(Ursina):
    BOARD_SIDE = 60
    time = 0

    class Entity(Entity):
        def __init__(self,b,**kwargs):
            super().__init__(**kwargs)
            print(len(scene.entities).__str__())
            b['value']=len(scene.entities)/1700
    class File:
        def __init__(self, filepath):
            self.path = filepath

        @property
        def ro(self):
            return open(self.path, "r")

        @property
        def wo(self):
            return open(self.path, "w")

        def repwrite(self, text):
            json.dump(obj=text, fp=self.wo, indent=4)

        @property
        def text(self):
            return self.ro.read()

        @text.setter
        def text(self, value):
            json.dump(obj=value, fp=self.wo, indent=4)

        @property
        def size_bytes(self):
            return len(self.text.encode("utf-8"))

        @property
        def size_bytes_kb(self):
            return len(self.text.encode("utf-8")) / 1024

        @property
        def size_bytes_mb(self):
            return len(self.text.encode("utf-8")) / (1024 * 1024)

        @property
        def size_bytes_gb(self):
            return len(self.text.encode("utf-8")) / (1024 * (1024 * 1024))

        @property
        def dict_sizes(self):
            return {"b": self.size_bytes,
                    "kb": self.size_bytes_kb,
                    "mb": self.size_bytes_mb,
                    "gb": self.size_bytes_gb}

    class UiTablet:
        highlight_index = 0
        current_program = ""
        pg_enties = [[], [], [], [], [], [], []]
        aspect_y = window.aspect_ratio
        aspect_x = 1
        resolution = window.screen_resolution
        COLORS = [color.rgb(200, 200, 200), color.rgb(125, 125, 125), color.rgb(200, 200, 200)]
        TOKEN_COLORS = [color.red, color.cyan, color.green, color.yellow]

        class Coords(Vec3):
            def __init__(self, x, z):
                xAxis = x - 1
                zAxis = z - 1
                super().__init__(xAxis, 0, zAxis)

            def break_dict(self):
                return {"x": self.x, "z": self.z}

        SAFE_MODE_COORDS = {"green": [Coords(3, 7), Coords(7, 2)],
                        "yellow":[Coords(13, 9), Coords(9, 14)],
                        "blue": [Coords(9, 3), Coords(14, 7)],
                        "red":  [Coords(7, 13), Coords(2, 9)]}
        safePositions = []
        pathPoints = []
        ORDER = {
            "blue": "z",
            "red": "x",
            "green": "z",
            "yellow": "x"
        }

        ORDER_LIST = ["blue", "red", "green", "yellow"]
        my_unit = .5 / 60

        def Paragraph(self, p_list: list[str]):

            string = ""
            for val in p_list[:]:
                string += dedent(val).strip() + "\n"
            return string
        @property
        def turn(self) -> int:
            return self._turn
        @turn.setter
        def turn(self,value):
            self._turn = value
        def __init__(self, combineCaptureFtTime, switch,inp_val_list,turn):
            self.switch=switch
            self.NAMES = inp_val_list
            self.turn = turn
            self.label = Text(position=Vec3(0.1, .05, -.2), font="consola.ttf", size=Text.size, text="minimap.exe",
                              color=color.black)
            self.PG_NAME_LIST = ["minimap.exe", "dice_roll.exe", "switch_player.exe", "home", "console.exe", "help.exe",
                                 'credits.exe']
            self.PG_FUNCS = [self.draw_minimap, self.create_dice_roll, self.create_switch_player, None, self.create_console,
                             self.create_help, self.create_credits]
            self.PG_NAME_DICT = {
                "home": 3,
                "minimap.exe": 0,
                "dice_roll.exe": 1,
                "switch_player.exe": 2,
                "console.exe": 4,
                "help.exe": 5,
                "credits.exe": 6
            }
            Sequence(2, Func(self.switch_program, del_pg_name="minimap.exe", create_pg_name="help.exe")).start()
            self.e = None
            self.index = 0
            self.pieces = [[], [], [], []]
            self.TOKENS_STARTING_VEC = [[], [], [], []]
            self.VEC_NUM = [[[2, 2], [4, 2], [2, 4], [4, 4]],
                            [[15 - 2, 2], [15 - 4, 2], [15 - 2, 4], [15 - 4, 4]],
                            [[2, 15 - 2], [4, 15 - 2], [2, 15 - 4], [4, 15 - 4]],
                            [[15 - 2, 15 - 2], [15 - 4, 15 - 2], [15 - 2, 15 - 4], [15 - 4, 15 - 4]]]
            self.START_VEC = Vec2((-.0865 + (self.my_unit / 2)) - (self.my_unit - (self.my_unit * 30)),
                                  -(.20 + (self.my_unit + (self.my_unit * 30))))
            self.suggestions = []
            for i in self.rangelen(self.VEC_NUM):
                li1 = self.VEC_NUM[i]
                li2 = self.TOKENS_STARTING_VEC[i]
                for j in self.rangelen(self.VEC_NUM):
                    vecobj = li1[j]
                    vec = self.minimap_Vec(vecobj[0] * 2, vecobj[1] * 2)
                    li2.append(Vec3(vec.x, vec.y, -.01))


            self.h =Entity(parent=camera.ui, model="cube",
                   color=color.black, scale=(0.7, 0.85), position=Vec2(0.39, -0.3))
            self.c = Entity(parent=camera.ui, model="cube",
                            color=color.white, scale=(0.6, 0.75), position=Vec3(0.39, -0.3, -.0025))

            self.MINIMAP_COLORS = [color.black, color.white]
            self.M_COLORS = [color.yellow,color.green, color.red,color.cyan  ]
            self.n = .5
            self.txt = Text(text=combineCaptureFtTime(0) + f" {b}%", position=(0.3, .05, -.2), font="DS-DIGIT.TTF",
                            color=color.red)
            self.draw_minimap()
            self.console_text = "run "
            self.console_text_entity = None
            self.dice: Entity
        
        def create_credits(self):
            program_entities = self.pg_enties[self.PG_NAME_DICT["credits.exe"]]
            self.txt.text = "credits.exe"
            li = [
                "<white><scale:1.25>Credits",
                " Made in <image:python_logo.png><image>",
                "",
                "",
                "<scale:1> contributors of Development of Python",
                "<scale:0.75> CWI, CNRI, BeOpen.com,",
                "Zope Corporation and a cast of thousands.",
                "  See <rgb(0,0,238)>www.python.org<white> for more information",
                "<scale:1>plugins",
                "<scale:0.75>ursina engine to create 3d world of game",
                "json to stringify and parse objects to keep names as text",
                "plyer to give notification of game",
                "psutil to get system information like battery level",
                "to render on ui tablet",
                "<scale:1>dependencies of plugins",
                "<scale:0.75>ursina engine",
                "<scale:0.6>panda3d",
                "pyperclip",
                "pillow",
                "numpy",
                "screeninfo",
                "<scale:1>websites to tell how to do task of game",
                "<scale:0.75><rgb(0,0,238)>stackoverflow.com",
                "github.com",
                "geeksforgeeks.com",
                "stackoverflow.com",
                "w3schools.com",
                "<scale:1> <white>Programmer to create 3d ludo game"
            ]
            e = Entity(parent=camera.ui, model="quad", color=color.black, position=(self.c.x, self.c.y, -.01),
                       scale=(self.c.scale_x, self.c.scale_y - .1))

            self.e = Text(parent=camera.ui, position=(e.x - e.scale_x / 2, self.txt.y - (Text.size * 2), -.03),
                          font="consola.ttf", text=self.Paragraph(li))
            self.current_program = "credits.exe"

            texture_config = Texture("python_logo.png")
            self.e.images[0].scale = Vec2(texture_config.width / texture_config.height, 1)
            self.e.images[0].x += (texture_config.width / 2) / texture_config.height
            program_entities.append(self.e)
            program_entities.append(e)

        def create_console(self):

            program_entities = self.pg_enties[self.PG_NAME_DICT["console.exe"]]

            e = Entity(parent=camera.ui, model="quad", color=color.black, position=(self.c.x, self.c.y, -.01),
                       scale=(self.c.scale_x, self.c.scale_y - .1))
            self.console_text_entity = Text(parent=camera.ui,
                                            position=(e.x - e.scale_x / 2, self.txt.y - (Text.size * 10), -.03),
                                            font="consola.ttf", color=color.white, text=self.console_text)

            pos = self.console_text_entity.position
            for i in self.rangelen(self.PG_FUNCS):
                b = Button(parent=camera.ui,
                           position=(pos.x + .125, self.txt.y - (Text.size * 1) - (Text.size * (i + 1)), -.3),
                           text=self.PG_NAME_LIST[i], scale=(.25, Text.size), color=color.white)
                b.text_entity.color = color.black
                b.text_entity.font = "consola.ttf"
                b.text_entity.scale = Text.scale
                self.suggestions.append(b)
                program_entities.append(b)
                program_entities.append(self.console_text_entity)
            self.current_program = "console.exe"
            program_entities.append(e)
        
        def create_dice_roll(self):
            self.current_program = "dice_roll.exe"
            program_entities = self.pg_enties[self.PG_NAME_DICT["dice_roll.exe"]]
            self.dice = Entity(parent=camera.ui, model="dice", position=self.c.position, scale=.125,
                               texture=load_texture("d6"))
            program_entities.append(self.dice)
        def create_switch_player(self):
            self.index = 0
            self.current_program = "switch_player.exe"
            program_content_list = self.pg_enties[self.PG_NAME_DICT["switch_player.exe"]]
            self.broken_center_coords = self.coords_to_dict(self.Coords(8, 8))

            x = self.broken_center_coords["x"]
            z = self.broken_center_coords["z"]
            self.c_coords = [[], [], [], []]
            self.values = [[x + 1, x + 1, x + 1, x + 1, x + 1, x + 1], [x - 1, x - 1, x - 1, x - 1, x - 1, x - 1],
                           [x - 1, x - 1, x - 1, x - 1, x - 1, x - 1], [x + 1, x + 1, x + 1, x + 1, x + 1, x + 1]]
            for j in range(4):
                obj = self.values[j]
                for i in self.rangelen(obj):
                    if j == 1 or j == 2:
                        obj[i] -= i
                    elif j == 0 or j == 3:
                        obj[i] += i
            for i in self.rangelen(self.values):
                obj = self.values[i]
                o = self.ORDER_LIST[i]
                for num in obj[:]:
                    if self.ORDER[o] == "x":
                        self.c_coords[i].append(self.Coords(num, z))
                    elif self.ORDER[o] == "z":
                        self.c_coords[i].append(self.Coords(x, num))

            for i in range(15):
                for j in range(15):
                    m_vec = self.minimap_Vec(i * 2, j * 2)
                    e = Entity(parent=camera.ui, model="cube", scale=self.my_unit * 2, collider="box",
                               texture="border_texture",
                               color=color.rgb(255, 255, 255), position=Vec3(m_vec.x, m_vec.y, -.005))
                    program_content_list.append(e)

                    for c in self.rangelen(self.c_coords):
                        obj = self.c_coords[c]
                        for coords in obj[:]:
                            if self.Coords(i, j) == coords:
                                e.color = self.M_COLORS[c]
                    for index in self.rangelen(self.SAFE_MODE_COORDS["red"]):
                        if i < 6 and j < 6:
                            e.color = color.red
                            e.texture = None
                        if i > 14 - 6 and j < 6:
                            e.color = color.cyan
                            e.texture = None
                        if i < 6 and j > 14 - 6:
                            e.color = color.green
                            e.texture = None
                        if i > 14 - 6 and j > 14 - 6:
                            e.color = color.yellow
                            e.texture = None

                        if Vec3(i, 0, j) == self.SAFE_MODE_COORDS["green"][index]:
                            self.safePositions.append(e)
                            self.pathPoints.append(e)
                            e.color = color.red
                            e.texture = None
                        if Vec3(i, 0, j) == self.SAFE_MODE_COORDS["blue"][index]:
                            self.safePositions.append(e)
                            self.pathPoints.append(e)
                            e.color = color.cyan
                            e.texture = None
                        if Vec3(i, 0, j) == self.SAFE_MODE_COORDS["red"][index]:
                            self.safePositions.append(e)
                            self.pathPoints.append(e)
                            e.color = color.green
                            e.texture = None
                        if Vec3(i, 0, j) == self.SAFE_MODE_COORDS["yellow"][index]:
                            self.safePositions.append(e)
                            self.pathPoints.append(e)
                            e.color = color.yellow
                            e.texture = None
                    if not (e.texture == None and (e not in self.safePositions)):
                        self.index += 1
                    
            for i in range(4):
                for j in range(4):
                    e = Entity(parent=camera.ui, model="sphere", scale=self.my_unit * 1,
                               position=self.TOKENS_STARTING_VEC[i][j],
                               color=self.TOKEN_COLORS[i])
                    program_content_list.append(e)
                    e.shader = basic_lighting_shader
                    print(len(self.pieces[0]))
                    if not(len(self.pieces[i]) == 4):
                        self.pieces[i].append(e)
                    else:
                        self.pieces[i][j] = e
            p = Entity(rotation_z=-45)
            p1 = Entity(parent=p, y = -.5)
            vts = [[Vec3()],[Vec3()],[Vec3()],[Vec3()]]
            tris = [[],[],[],[]]
            for i in range(4):
                for j in range(8):
                    if j!=7:
                        tris[i].append((0,j,j+i))
                    p.rotation_z+=360/32
                    vts[i].append(p1.world_position) 
            for i in range(4):
                Entity(parent=camera.ui,model=Mesh(vertices=vts[i],triangles=tris[i]),position=(.33,.33),scale=.5)
            #t = (((i/90 for i in range(90)),(i/90 for i in range(90))),((),()),((),()),((),()))
            # p = Entity(position=(.33,.33,-.1))
            # p1 = Entity(parent=p, y = .15)
            # vecs = [Vec3(.33,.48)]
            # for i in range(4):
            #     p.rotation_z+=90
            #     Entity(parent=camera.ui,model=Cone(2),rotation_y=90,position=p1.world_position,scale=.15,rotation_z=180+p.rotation_z,color=self.darken(self.M_COLORS[i],i*25))
        def brighten(self,c,amount=50):
            v = []
            for i in ("r","g","b"):
                if (getattr(c,i)*255)+amount>255:
                    v.append(255)
                else:
                    v.append((getattr(c,i)*255)+amount)
            return color.rgb(v[0],v[1],v[2])
        def darken(self,c,amount=50):
            v = []
            for i in ("r","g","b"):
                if (getattr(c,i)*255)-amount<0:
                    v.append(0)
                else:
                    v.append((getattr(c,i)*255)-amount)
            return color.rgb(v[0],v[1],v[2])
        
        def create_help(self):
            self.current_program = "help.exe"
            li = ["<scale:1.25>Help",
                  "<scale:1>There are 5 programs in tablet:-",
                  "1. help.exe",
                  "<scale:0.75>it tells info about programs",
                  "<scale:1>2. switch_player.exe",
                  "<scale:0.75>It helps to switch players",
                  "<scale:1>3. minimap.exe",
                  "<scale:0.75>It helps to know the minimap of ludo board",
                  "<scale:1>4. console.exe",
                  "<scale:0.75>It is the console that executes programs",
                  "<scale:1>5. dice_roll.exe",
                  "<scale:0.75>It rolls dice",
                  "<scale:1>shortcuts",
                  "<scale:0.75>1. self key to reach home",
                  "2. m key to run minimap.exe",
                  "3. c key to run switch_player.exe",
                  "4. e key to run console.exe",
                  "5. r key to run dice_roll.exe",
                  "6. h key to run help.exe"]

            e = Entity(parent=camera.ui, model="quad", color=color.black, position=(self.c.x, self.c.y, -.01),
                       scale=(self.c.scale_x, self.c.scale_y - .1))
            program_entities = self.pg_enties[self.PG_NAME_DICT["help.exe"]]
            text = Text(parent=camera.ui, position=(e.x - e.scale_x / 2, self.txt.y - (Text.size * 2), -.03),
                        font="consola.ttf", color=color.white, text=self.Paragraph(li))
            program_entities.append(text)
            program_entities.append(e)

        def delete_program(self, program_name):
            try:
                for entity in self.pg_enties[self.PG_NAME_DICT[program_name]]:
                    destroy(entity)
                self.pg_enties[self.PG_NAME_DICT[program_name]] = []
            except:
                raise NameError("program_name is not found in UiTablet.PG_NAME_DICT")

        def run_program(self, program_name):
            try:
                self.PG_FUNCS[self.PG_NAME_DICT[program_name]]()
                self.label.text = program_name
            except Exception as e:
                raise e

        def switch_program(self, **kwargs):
            del_pg_name = kwargs["del_pg_name"]
            create_pg_name = kwargs["create_pg_name"]
            self.delete_program(del_pg_name)
            self.run_program(create_pg_name)

        def coords_to_dict(self, coords: Vec3):
            return {"x": coords.x, "y": coords.y, "z": coords.z}

        def minimap_Vec(self, x, y):
            my_unit_Vec2 = Vec2(x, y)

            coords = {"x": my_unit_Vec2.x, "y": my_unit_Vec2.y}
            return Vec2((coords["x"] * self.my_unit) + self.START_VEC.x,
                        (coords["y"] * self.my_unit) + self.START_VEC.y)

        def mid(self, num):
            if num / 2 != ceil(num / 2):
                return (num / 2) + 0.5
            else:
                raise TypeError("Number given is not odd")

        def rangelen(self, exp):
            return range(len(exp))
        def combine_lists(self, list: list[list]):
            l = []
            for obj in list[:]:
                for val in obj[:]:
                    l.append(val)
            return l
        def draw_minimap(self):
            self.index = 0
            self.current_program = "minimap.exe"
            program_content_list = self.pg_enties[0]
            self.broken_center_coords = self.coords_to_dict(self.Coords(8, 8))

            x = self.broken_center_coords["x"]
            z = self.broken_center_coords["z"]
            self.c_coords = [[], [], [], []]
            self.values = [[x + 1, x + 1, x + 1, x + 1, x + 1, x + 1], [x - 1, x - 1, x - 1, x - 1, x - 1, x - 1],
                           [x - 1, x - 1, x - 1, x - 1, x - 1, x - 1], [x + 1, x + 1, x + 1, x + 1, x + 1, x + 1]]
            for j in range(4):
                obj = self.values[j]
                for i in self.rangelen(obj):
                    if j == 1 or j == 2:
                        obj[i] -= i
                    elif j == 0 or j == 3:
                        obj[i] += i
            for i in self.rangelen(self.values):
                obj = self.values[i]
                o = self.ORDER_LIST[i]
                for num in obj[:]:
                    if self.ORDER[o] == "x":
                        self.c_coords[i].append(self.Coords(num, z))
                    elif self.ORDER[o] == "z":
                        self.c_coords[i].append(self.Coords(x, num))

            for i in range(15):
                for j in range(15):
                    m_vec = self.minimap_Vec(i * 4, j * 4)
                    e = Button(model="cube", scale=self.my_unit * 4, collider="box",
                               texture="border_texture",
                               color=color.rgb(255, 255, 255), position=Vec3(m_vec.x, m_vec.y, -.005))
                    program_content_list.append(e)

                    for c in self.rangelen(self.c_coords):
                        obj = self.c_coords[c]
                        for coords in obj[:]:
                            if self.Coords(i, j) == coords:
                                e.color = self.M_COLORS[c]
                    for index in self.rangelen(self.SAFE_MODE_COORDS["red"]):
                        if i < 6 and j < 6:
                            e.color = color.red
                            e.texture = None
                        if i > 14 - 6 and j < 6:
                            e.color = color.cyan
                            e.texture = None
                        if i < 6 and j > 14 - 6:
                            e.color = color.green
                            e.texture = None
                        if i > 14 - 6 and j > 14 - 6:
                            e.color = color.yellow
                            e.texture = None

                        if Vec3(i, 0, j) == self.SAFE_MODE_COORDS["green"][index]:
                            self.safePositions.append(e)
                            self.pathPoints.append(e)
                            e.color = color.red
                            e.texture = None
                        if Vec3(i, 0, j) == self.SAFE_MODE_COORDS["blue"][index]:
                            self.safePositions.append(e)
                            self.pathPoints.append(e)
                            e.color = color.cyan
                            e.texture = None
                        if Vec3(i, 0, j) == self.SAFE_MODE_COORDS["red"][index]:
                            self.safePositions.append(e)
                            self.pathPoints.append(e)
                            e.color = color.green
                            e.texture = None
                        if Vec3(i, 0, j) == self.SAFE_MODE_COORDS["yellow"][index]:
                            self.safePositions.append(e)
                            self.pathPoints.append(e)
                            e.color = color.yellow
                            e.texture = None
                    if not (e.texture == None and (e not in self.safePositions)):
                        e.text = str(self.index)
                        e.text_entity.color = color.black
                        e.text_entity.size = Text.size / 3
                        self.index += 1
            for i in range(4):
                for j in range(4):
                    e = Entity(parent=camera.ui, model="sphere", scale=self.my_unit * 2,
                               position=self.TOKENS_STARTING_VEC[i][j],
                               color=self.TOKEN_COLORS[i])
                    program_content_list.append(e)
                    e.shader = basic_lighting_shader
                    print(len(self.pieces[0]))
                    if not(len(self.pieces[i]) == 4):
                        self.pieces[i].append(e)
                    else:
                        self.pieces[i][j] = e
    def captureFtTime(self, string: str, intSec: int):
        if string == "H":

            if len(str(12 + ((intSec // 3600) % 24))) == 1:
                return "0" + str((12 + (intSec // 3600)) % 24)
            else:
                return str((12 + (intSec // 3600)) % 24)
        if string == "M":
            if len(str((intSec // 60) % 60)) == 1:
                return "0" + str((intSec // 60) % 60)
            else:
                return str((intSec // 60) % 60)

    def combineCaptureFtTime(self, intSec: int):
        intSec = round(intSec)
        return f"{self.captureFtTime('H', intSec)}:{self.captureFtTime('M', intSec)}:{intSec % 60} "

    class Flag:
        BOARD_SIDE = 60

        def __init__(self):
            self.f_index = 25
            self.parts = []

            self.e = Entity(parent=scene, model="cube", collider="box", scale=(0.1, 10, 0.1),
                            position=(28, 5, self.BOARD_SIDE / 2 - 2), color=color.color(60, 1, 1, 1))
            self.e.shader = basic_lighting_shader
            for i in range(100):
                self.parts.append(
                    Entity(parent=scene, model="cube",
                           scale=(0.01,
                                  (i + 1) * (5 / 200),
                                  0.01),
                           position=(int(self.e.position[0]),
                                     self.e.position[1] + (
                                                 (self.e.scale[1] / 3) + (((self.e.scale[2] / 200) * i) / 2)) - (
                                             ((i + 1) * (5 / 200)) / 2),
                                     self.e.position[2] + (i / 75)
                                     ),
                           rotation=(270, 0, 0),
                           color=color.red, shader=basic_lighting_shader
                           )
                )

    class Coords(Vec3):
        def __init__(self, x, z, add=False):
            xAxis, zAxis = x, z
            if not (add):
                xAxis = x - 1
                zAxis = z - 1
            super().__init__(xAxis, 0, zAxis)

        def break_dict(self):
            return {"x": self.x, "z": self.z}

    SAFE_MODE_COORDS = {"green": [Coords(3, 7), Coords(7, 2)],
                        "yellow":[Coords(13, 9), Coords(9, 14)],
                        "blue": [Coords(9, 3), Coords(14, 7)],
                        "red":  [Coords(7, 13), Coords(2, 9)]}
    safePositions = []
    pathPoints = []
    ORDER = {
        "blue": "z",
        "red": "x",
        "green": "z",
        "yellow": "x"
    }

    class GameNotification(Button):
        def __init__(self, text="", timeout=2, **kwargs):
            super().__init__(size=10, text=text,**kwargs)
            self.z = -1
            self.fit_to_text()
            Sequence(timeout, Func(self.animate_color, color.rgba(0, 0, 0, 0), duration=1), 1,
                     Func(destroy, self)).start()
            Sequence(timeout, Func(self.text_entity.animate_color, color.rgba(0, 0, 0, 0), duration=1), 1,
                     Func(destroy, self.text_entity)).start()
    class TimeStamp(Button):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.color = color.black   
            self.text = self.time
            self.font = "DS-DIGIT.TTF"
            self.text_color = color.red
            self.text_entity.size = 1
            self.fit_to_text()
        @property
        def font(self):
            return self.text_entity.font
        @font.setter
        def font(self, value):
            self.text_entity.font = value
        @property
        def time(self):
            return time.strftime("%H:%M:%S")
        def update(self):
            self.text = self.time
            self.fit_to_text()
    class Hill(Entity):
        def __init__(self,b,**kwargs):
            super().__init__(b=b,parent=scene, model="sphere",**kwargs)

    ORDER_LIST = ["blue", "red", "green", "yellow"]
    URSINA_COLORS_LIST = [value for key, value in color.colors.items()]

    def __init__(self):
        self.code = ""
        self.btry = None
        self.clouds = []
        self.lift = None
        self.j = 0
        self.is_stuck_to_player = False
        self.switch_index = 0
        self.r = None
        self.timestamp = None
        self.xseq = [6,2,1,5]
        self.yseq = [6,4,1,3]
        self.seqs = []
        self.turn = 0
        self.index = 0
        
        self.names = {"teams": [],
                      "player": []}
        self.entity_index_pathpoints: list[list[int]]
        self.entity_pathpoints: list[list[Entity]] = [[], [], [], []]
        self.vec_pathpoints = [[[], [], [], []], [[], [], [], []], [[], [], [], []], [[], [], [], []]]
        self.posindexes = [[[0] * 4 for _ in range(4)] for _ in range(4)]
        self.TOKEN_COLORS = [color.red,color.cyan , color.green,color.yellow ]
        self.VEC_NUM = [[[2, 2], [4, 2], [2, 4], [4, 4]],
                        [[15 - 2, 2], [15 - 4, 2], [15 - 2, 4], [15 - 4, 4]],
                        [[2, 15 - 2], [4, 15 - 2], [2, 15 - 4], [4, 15 - 4]],
                        [[15 - 2, 15 - 2], [15 - 4, 15 - 2], [15 - 2, 15 - 4], [15 - 4, 15 - 4]]]
        self.TOKENS_STARTING_VEC = [[], [], [], []]

        for i in self.rangelen(self.VEC_NUM):
            li1 = self.VEC_NUM[i]
            li2 = self.TOKENS_STARTING_VEC[i]
            for j in self.rangelen(self.VEC_NUM):
                vecobj = li1[j]
                li2.append(Vec3(vecobj[0] * 4, 4, vecobj[1] * 4))
        self.f = self.File("storage.json")
        self.freq = random.randrange(10,25)
        if len(self.f.ro.read()) == 0:
            self.f.text = self.names
        self.names = json.loads(self.f.text)
        self.names_list = json.load(self.f.ro)['player']
        self.team_list = json.load(self.f.ro)['teams']
        self.txt = None
        self.p = []
        
        self.b_entity = None
        self.bl_entity = None
        self.is_transition_in_process = False
        self.q = None
        self.pos = Vec3(0, 0, 0)
        self.switched = False
        self.anim_index = 0
        self.drawen_board = False
        self.board = None
        self.rot = 90
        self.v1 = False
        self.t = None
        self.l_enties = []
        self.COLORS = [color.yellow,color.green, color.red,color.cyan  ]
        self.asked_input_fields=False
        self.combined_inps = []
        self.GAME_ORDER_LIST = ["red","blue","green","yellow"]
        self.flag = None
        # time.sleep(10)
        # self.n = Network()
        # self.p = self.read_pos(self.n.getPos())
        super().__init__()
        self.objs=['Asteroid1.obj', 'Asteroid2.obj', 'Asteroid3.obj', 'BigAsteroid.obj', 'BiggerAsteroid.obj', 'Moon.obj', 'Planet1.obj', 'Planet2.obj', 'Planet3.obj', 'SmallMoon.obj', 'SmallPlanet1.obj', 'SmallPlanet2.obj']
        self.planet_objs = ['BigBush.obj', 'BigTreeWithLeaves.obj', 'Cloud1.obj', 'Cloud2.obj', 'Cloud3.obj', 'EveryModel.obj', 'SmallBush.obj', 'SmallTreeWithLeave.obj', 'TreeNoLeavesBig.obj', 'TreeNoLeavesSmall.obj']
        self.rocket=None
        self.bgm_audio = Audio("3d ludo bgm",loop=True)
        self.dice_roll_audio = Audio("roll",autoplay=False,loop=False)
        self.at = 0
        self.hbar = None
       
        self.fps = self.FPS()
        self.tablet = None
        self.player = None
        self.M_SCALE = (.5, .5)
        self.M_START_POS = (-.5, -.25)
        self.M_END_POS = (self.M_START_POS[i]+self.M_SCALE[i] for i in range(2))
        self.sky = Entity(parent=scene,model="sky_dome",texture="sky",double_sided=True,scale=2000,visible=False)
        Sky(texture="sky1",double_sided=True,scale=50000)
        self.pieces: list[list[Entity]] = [[], [], [], []]
        self.sun = None
        window.fps_counter.color = color.black
        self.moon = None
        self.i = 0
        self.btns = []
        self.inp_val_list = [[], [], [], [], []]
        self.inp_list = [[], [], [], [], []]
        self.alphabets =   """ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"""
        self.emojis =        "ßΓπΣµτΦΘΩδ∞φε∩≡±≥≤⌠⌡≈°··√ⁿ■ €„…†‡‰ŠŒŽ“”—™šœžŸ¤¦¨©¯²³·¹¼½¾ÀÁÂÃÄÅÆÇÈÉÊËÌÍÏÏÐÒÓÔÕÖØÙÚÛÜÝÞ♠àáâãäåæç"
        self.decrypt_dict = {self.emojis[index]: self.alphabets[index] for index in self.rangelen(self.alphabets)}
        self.encrypt_dict = {self.alphabets[index]: self.emojis[index] for index in self.rangelen(self.alphabets)}
        self.perm  = []
        self.tk = None
        for i in range(255):
            self.perm.append(random.randrange(0,100))    
        self.btn = None
        self.m_player = None
        self.t = None
        self.space_trans()
    class Timer(Button):
        
        def __init__(self,end_func,**kwargs):
            self.i = 0
            self.f = Func(end_func)
            self.ms = 30000
            self.s = 0
            self.t = int(time.time()*1000)
            self.maxval = 30000
            super().__init__(text="0.0000s",scale = (Text.size*20, Text.size),position=(-.45 * window.aspect_ratio, .45),color=color.red,origin = (-.5, .5),**kwargs)
            self.bar = Entity(parent=self,scale=(0,1), model='quad', z=-.01, color=color.green,origin=self.origin,**kwargs)
        @property
        def val(self):
            return (self.bar.scale_x/self.scale_x)*self.maxval
        @val.setter
        def val(self, value):
            self.bar.scale_x = value/self.maxval
            self.text_entity.text = f"{('0'*(2-len(str(ceil(value/1000)))))+str(ceil(value/1000))}.{('0'*(4-len(str(value % 1000))))+str(value % 1000)}s"
        def loop(self):
            if self.ms > 0:
                self.ms=self.maxval-(int(time.time()*1000)-self.t)
                self.val = self.ms
            if self._finished:
                self.text_entity.text = "Time Up!"
            if self.finished and self.i<1:
                self.disable()
                self.f()
                self.i+=1
        @property
        def finished(self):
            return int(self.t/1000)-int(time.time()) == -31            
        @property
        def _finished(self):
            return int(self.t/1000)-int(time.time()) < -30 and not self.finished            
        
    class FPS(Button):
        def getcolor(self,val):
            if val < 30:
                return lerp(self.DANGER_COLOR,self.MILD_COLOR,val/30)
            elif val<60:
                return lerp(self.MILD_COLOR,self.NORMAL_COLOR,(val-30)/30)
            if val>=60:
                return self.NORMAL_COLOR
        
        class Algorithm:
            class AlgebraVarNotFoundError(ValueError):
                def __init__(self,key,expr):
                    v = "no %s variable in expression %s"%key, expr
                    super().__init__(v)
            class AlgebraVarIncompleteError(ValueError):
                def __init__(self,expr,kwargs):
                    v = "incomplete variable length "+expr+" "+str(kwargs)
                    super().__init__(v)
            def __init__(self,expr:str):
                self.expr = expr
                self.alphabets = list("abcdefghijklmnopqrstuvwxyz")
                self.vars = [v for v in self.alphabets if v in self.expr]    
            def __call__(self,**kwargs):
                s = self.expr 
                if len(kwargs) != len(self.vars):
                    raise self.AlgebraVarIncompleteError("incomplete variable length ",self.expr,kwargs) 
                for key,value in kwargs.items():
                    if key not in self.vars:
                        raise self.AlgebraVarNotFoundError(key, self.expr)
                    s=s.replace(key,str(value))
                return eval(s)

        def __init__(self,res:int=100,**kwargs):
            self.i = 0
            
            self.maxval = 60
            p,q = -45,-45
            
            self.DANGER_COLOR = color.red
            self.MILD_COLOR = color.yellow
            self.NORMAL_COLOR = color.rgb(0,125,0)
            a = self.Algorithm("(1/r)*i")
            self.COLOR = [lerp(self.DANGER_COLOR,self.MILD_COLOR,a(r=res,i=i)) for i in range(1,res+1)]
            self.COLOR.extend([lerp(self.MILD_COLOR,self.NORMAL_COLOR,a(r=res,i=i)) for i in range(1,res+1)])
            print(self.COLOR)
            self.SIZE= 1/(res*2)
            print(self.SIZE)
            self.res=res
            self.fps = 60
            self.t = int(time.time()*1000)
            super().__init__(text="FPS=60",position=(0,.325),scale = .25,color=color.white,**kwargs)
            pt = Entity(rotation_z=-45)
            pt2 = Entity(parent=pt,x=-.5)
            
            EditorCamera()
            self.e = []
            
            e = self.e
            for _ in range(res*2):
                e.append(pt2.world_position)
                pt.rotation_z+=270/(res*2)
            self.model = Mesh(vertices=e,colors=self.COLOR,mode='line',thickness=2)
            self.p = Entity(parent=self,model=Circle(),scale=(.025,.025),color=color.white)
            self.bar = Entity(parent=self.p,scale=(.5,14),position=(0,4.25),model='quad', z=-.02, color=color.white,origin=self.origin,**kwargs)
        @property
        def val(self):
            return ((self.p.rotation_z+175)/350)*60
        def animate_text(self,val,duration=1):
            res = val-int(self.text[4:])
            s = Sequence()
            j = int(self.text[4:])

            for i in range(abs(res)):
                s.append(duration / res)
                if res<0:
                    j-=1
                    s.append(Func(setattr,self,'text',f"FPS={j}"))
                    s.append(Func(setattr,self.text_entity,'color',self.getcolor(j)))
                else:
                    j+=1
                    s.append(Func(setattr,self, 'text', f"FPS={j}"))
                    s.append(Func(setattr, self.text_entity, 'color', self.getcolor(j)))
            s.start()
            return s
        @val.setter
        def val(self, value):
            if value<self.maxval:
                self.p.animate_rotation_z(-135+((270/60)*value),duration=1,curve=curve.linear)
            else:
                self.p.animate_rotation_z(135,duration=1,curve=curve.linear)
            self.animate_text(value)
        def loop(self):
            if self.i > 60:
                self.val = int(1//time.dt)
                self.i = 0
            self.i+=1
        @property
        def finished(self):
            return int(self.t/1000)-int(time.time()) == -31
                
    class Arc(Mesh):
        def __init__(self,start_deg=0,deg=360,res=16,pos=Vec3(),**kwargs):
            p = Entity(rotation_z=start_deg)
            p1 = Entity(parent=p,y=.5)
            vts = []
            for i in range(res+1):
                p.rotation_z = lerp(start_deg,deg,i/res)
                vts.append(p1.world_position)
            super().__init__(vertices=vts,mode="line",**kwargs)
            destroy(p)
    class Cloud(Entity):
        def stop_rain(self):
            self.rain_animator.loop = False
        def rain(self):
            for _ in range(10):
                e = Entity(parent=self,model="sphere",scale=.01,x=random.uniform(.5,-1),z=random.uniform(-.5,.5),color=color.rgb(0,255,255,125))
                
                self.rain_animator = e.animate('world_y',0,duration=1,delay=random.uniform(0,2),loop=True)
        def ind_color(self,b,c,d,m,a=255):
            if m == 1:
                return Color(b,c,d,a/255)
            else:
                return Color(b/m,c/m,d/m,a/255)
        
        def __init__(self,density,resolution=16,**kwargs):
            self.rain_animator = None 
            super().__init__(**kwargs)
            self.rain()
            Sequence(40,Func(self.stop_rain))
            self.dres = {"density":density,"resolution":resolution}
            self.kwargs=kwargs
            # vts = []
            # for _ in range(resolution):
            #     vts.append(Vec3(*(random.uniform(-.5,.5) for _ in range(3))))
            t = Texture("white.png")
            pts = []
            for _ in range(resolution):
                x,y = random.randrange(0,t.width),random.randrange(0,t.height)
                if t.get_pixel(x,y)==color.black:
                    continue
                else:
                    t.set_pixel(x,y,color.black)
                    pts.append((x,y))
                    t.apply()
            
            for v in range(t.width):
                for j in range(t.height):
                    distances = []
                    for i in pts[:]:
                        distances.append(distance2d((v,j),i))
                    b = sorted(distances)
                    noise = b[0]
                    t.set_pixel(v,j,self.ind_color(noise,noise,noise,b[len(b)-1],(noise/b[len(b)-1])*255).invert())
                    t.apply()
            self.texture=t
            Entity(parent=self,x=-.5)
            Entity(parent=self,x=-.25,y=.5)
            # self.model=Mesh(mode="line",vertices=vts)
            self.rain_animator = None
            self.alpha = density
            self.color = color.white
            self.shader=shaders.lit_with_shadows_shader
    class Rainbow(Entity):
        VIBGYOR_COLORS = [color.violet,color.hex("#4b0082"),color.blue,color.green,color.yellow,color.orange,color.red]   
        VIBGYOR_COLORS.reverse()
        @property
        def a(self):
            return self.l[0].alpha
        @a.setter
        def a(self,value):
            for i in self.l:
                i.alpha = value
           
        def __init__(self,Arc,**kwargs):
            super().__init__(double_sided=True,colors=self.VIBGYOR_COLORS,visible_self=False,shader=shaders.lit_with_shadows_shader,z=2000,**kwargs)
            self.l = []
            for i in range(7):
                self.l.append(Entity(b=kwargs["b"],parent=self,scale=(1,1,1),model=Arc(start_deg=-90,deg=90,thickness=5),double_sided=True,y=(4/75)-(i/75),color=self.VIBGYOR_COLORS[i],shader=shaders.lit_with_shadows_shader))
                print(self.VIBGYOR_COLORS[i])
    @classmethod
    def inverse_list(self,list):
        return [list[i] for i in self.range(len(list)-1,0,-1)]
    def mpos(self,x,y):
        my_unit_Vec2 = Vec2(x, y)

        coords = {"x": my_unit_Vec2.x, "y": my_unit_Vec2.y}
        return Vec2((coords["x"]/1000),
                    (coords["y"]/1000))
    def mscale(self,x,y):
        my_unit_Vec2 = Vec2(x, y)

        coords = {"x": my_unit_Vec2.x, "y": my_unit_Vec2.y}
        return Vec2(x/1000,y/1000)
    def dec(self, binary):
        int_val, i, n = 0, 0, 0
        while (binary != 0):
            a = binary % 10
            int_val = int_val + a * pow(2, i)
            binary = binary // 10
            i += 1
        return int_val
    def replace(self,li:list,remval,repval):
        li[li.index(remval)] = repval

    def decrypt(self, string: str):
        c = ""
        for char in string:
            c+=self.decrypt_dict[char]
        return c

    def encrypt(self, string: str):
        c = ""
        for char in string:
            c+=self.encrypt_dict[char]
        return c
    class Speedometer(Button):
        def getcolor(self,val):
            if val < 540:
                return lerp(self.NORMAL_COLOR,self.MILD_COLOR,val/30)
            elif val<180:
                return lerp(self.MILD_COLOR,self.DANGER_COLOR,(val-30)/30)
        class Algorithm:
            class AlgebraVarNotFoundError(ValueError):
                def __init__(self,key,expr):
                    v = "no %s variable in expression %s"%key, expr
                    super().__init__(v)
            class AlgebraVarIncompleteError(ValueError):
                def __init__(self,expr,kwargs):
                    v = "incomplete variable length "+expr+" "+str(kwargs)
                    super().__init__(v)
            def __init__(self,expr:str):
                self.expr = expr
                self.alphabets = list("abcdefghijklmnopqrstuvwxyz")
                self.vars = [v for v in self.alphabets if v in self.expr]    
            def __call__(self,**kwargs):
                s = self.expr 
                if len(kwargs) != len(self.vars):
                    raise self.AlgebraVarIncompleteError("incomplete variable length ",self.expr,kwargs) 
                for key,value in kwargs.items():
                    if key not in self.vars:
                        raise self.AlgebraVarNotFoundError(key, self.expr)
                    s=s.replace(key,str(value))
                return eval(s)

        def __init__(self,res:int=100,**kwargs):
            self.i = 0
            
            self.maxval = 1080
            p,q = -45,-45
            
            self.DANGER_COLOR = color.red
            self.MILD_COLOR = color.yellow
            self.NORMAL_COLOR = color.rgb(0,125,0)
            a = self.Algorithm("(1/r)*i")
            self.COLOR = [lerp(self.NORMAL_COLOR,self.MILD_COLOR,a(r=res,i=i)) for i in range(1,res+1)]
            self.COLOR.extend([lerp(self.MILD_COLOR,self.DANGER_COLOR,a(r=res,i=i)) for i in range(1,res+1)])
            print(self.COLOR)
            self.SIZE= 1/(res*2)
            print(self.SIZE)
            self.res=res
            self.fps = 60
            self.t = int(time.time()*1000)
            super().__init__(text="Kmph:0",position=(0,-.325),scale = .25,color=color.white,**kwargs)
            pt = Entity(rotation_z=-45)
            pt2 = Entity(parent=pt,x=-.5)
            self.e = []
            
            e = self.e
            for _ in range(res*2):
                e.append(pt2.world_position)
                pt.rotation_z+=270/(res*2)
            self.model = Mesh(vertices=e,colors=self.COLOR,mode='line',thickness=2)
            self.p = Entity(parent=self,model=Circle(),scale=(.025,.025),color=color.white)
            self.bar = Entity(parent=self.p,scale=(.5,14),position=(0,4.25),model='quad', z=-.02, color=color.white,origin=self.origin,**kwargs)
        @property
        def val(self):
            return ((self.p.rotation_z+175)/350)*1080

        @val.setter
        def val(self, value):
            if value<self.maxval:
                self.p.rotation_z = -135+(270/1080)*value
            else:
                self.p.rotation_z = 135
            self.text=f"Kmph:{value}"
        
            
    def ask_input_fields(self):
        
        n = ["Online multiplayer", "play with friends", "pass-N-play"]
        print(self.percentage_of_modules_used)
        pos = [Vec2(-.25, .25), Vec2(.25, .25), Vec2(-.25, -.25)]
        for i in range(3):
            b = Button(position=pos[i], text=n[i])
            b.tooltip = Tooltip(n[i])
            if b.text != "":
                b.fit_to_text()
                self.btns.append(b)
            else:
                destroy(b)
        Cursor()
        self.sky.visible=True
        self.btns[0].on_click = self.passNplay
        self.btns[2].on_click = self.passNplay
        self.asked_input_fields=True
    def passNplay(self):
        for btn in self.btns:
            destroy(btn)
        for i in range(4):
            inp = InputField(parent=camera.ui, default_value=f"{self.ORDER_LIST[i]} team name",
                             position=Vec2(-((window.aspect_ratio / 2) - .25), (i - 1.5) * .225),
                             scale=Vec2(.5, Text.size * 2))
            self.combined_inps.append(inp)
            self.inp_list[0].append(inp)
            index = 0
            for j in range(2):
                for r in range(2):
                    index += 1
                    sinp = InputField(parent=camera.ui, scale=Vec2(.55, Text.size * 2),
                                      position=Vec2(r * .5, ((i - 1.5) * .2215) + j * (Text.size * 2)),
                                      default_value=f"{self.ORDER_LIST[i]} team's token {index} name")
                    self.combined_inps.append(sinp)
                    self.inp_list[i + 1].append(sinp)
        self.b = Button(text="Start game", scale=Vec2(.05, .025))
        self.b.fit_to_text()
        self.b.on_click = self.draw_board
 
    def gravity(self,index):
        self.is_transition_in_process = False
        self.bl_entity.visible = False
        self.switch_index = index
        self.is_stuck_to_player = True
        
    def add_player_name_to_storage(self, name):
        if not (self.encrypt(name) in self.names["player"]):
            self.names["player"].append(self.encrypt(name))
            self.f.text = self.names
        else:
            pass

    def add_team_name_to_storage(self, name):
        if not (self.encrypt(name) in self.names["teams"]):
            self.names["teams"].append(self.encrypt(name))
            self.f.text = self.names
        else:
            pass
    def shake_trans(self,entity): 
        self.b_entity
    def keep_player_with_token(self,index):
        self.player.speed = 0
        self.player.gravity = False
        p = self.combine_lists(self.pieces)[index].position
        p.y = 4
        self.ppos = p
    @property
    def ppos(self):
        return self.player.world_position
    @ppos.setter
    def ppos(self, value):
        self.player.world_position = value 
    def switch_trans(self, position: Vec3, duration=2):

        self.ppos = position
        self.bl_entity.animate_color(color.rgb(0, 0, 0, 0), duration=duration, curve=curve.linear)
    
    
    
    def switch(self,index, duration=2):
        position  =self.combine_lists(self.pieces)[index].position
        position.y = 4
        self.is_transition_in_process = True
        if self.bl_entity is None:
            self.bl_entity = Entity(parent=camera.ui, model="cube", scale=(3, 3), color=color.rgb(0, 0, 0, 0))
        else:
            self.bl_entity.visible = True
        self.bl_entity.animate_color(color.rgb(0, 0, 0, 255), duration=duration, curve=curve.linear)
        Sequence(
            duration,
            Func(self.switch_trans, position, duration),
            duration,
            Func(self.gravity,index)
         ).start()
    
    def dice_roll(self):
        self.dice_roll_audio.play()
        self.tablet.dice.rotation = Vec3()
        v = random.randrange(1,7)  
        if v in self.xseq and not( v in self.yseq):
            self.tablet.dice.animate_rotation(Vec3(1800+(self.xseq.index(v)*90),1800,0),duration=self.dice_roll_audio.length,curve=curve.out_expo)
            print("xseq")
        elif v in self.yseq and not( v in self.xseq):
            self.tablet.dice.animate_rotation(Vec3(1800,1800+(self.yseq.index(v)*90),0),duration=self.dice_roll_audio.length,curve=curve.out_expo)
            print("yseq")
        elif v in self.xseq and v in self.yseq:
            print("xseq&yseq")
            if v == 1:
                self.tablet.dice.animate_rotation(Vec3(1980,1800,0),duration=self.dice_roll_audio.length,curve=curve.out_expo)
            else:
                self.tablet.dice.animate_rotation(Vec3(1800+(self.xseq.index(v)*90),1800+(self.yseq.index(v)*90),0),duration=self.dice_roll_audio.length,curve=curve.out_expo)
        print(v)
    def go_up(self,in_list:list[Entity]):
        for e in in_list:
            if e == self.player:
                e.speed=0
                e.gravity=False
                e.position=self.lift.position
            else:
                e.position=self.lift.position
        self.lift.animate_y(value=50,duration=5,curve=curve.linear)
        for e in in_list:
            e.animate_y(value=50,duration=5,curve=curve.linear)
        Sequence(7,Func(self.lift.animate_color,color.rgb(0,0,0,0),duration=3),3,Func(setattr,self.player,'speed',100),Func(setattr,self.player,'gravity',True),1,Func(setattr,self.lift,'color',color.yellow)).start()
    def go_down(self,in_list:list[Entity]):
        for e in in_list:
            if hasattr(e,'gravity'):
                e.speed=0
                e.gravity=False
                e.position=self.lift.position
            else:
                e.position=self.lift.position
        self.lift.animate_y(value=0,duration=5,curve=curve.linear)
        for e in in_list:
            e.animate_y(value=0,duration=5,curve=curve.linear)
        
        Sequence(5,self.lift.animate_color(color.rgb(0,0,0,0),duration=3),3,Func(setattr,self.player,'speed',100),Func(setattr,self.player,'gravity',True),1,Func(setattr,self.lift,'color',color.yellow)).start()
    def space_trans(self):
        t = Text(text="DivyanshGames presents \n 3d ludo",parent=scene,z=25*15,double_sided=True,scale=(10,10),color=color.white)
        for i in range(25):
            rand_choice = random.choice(self.objs)
            b = Entity(parent=scene,model=rand_choice,z=i*15,scale=1,x=random.randrange(-5,6,10),rotation_y=90,y=random.randrange(-5,6,10))
            if rand_choice.find("Planet")!=-1:
                b.texture="PlanetTexture"
            elif rand_choice.find("Asteroid")!=-1:
                b.color="#404040"
            elif rand_choice.find("Moon")!=-1:
                b.texture="MoonTexture"
            b.animate_z(-b.z,duration=(2*b.z)/50,curve=curve.linear)
            destroy(b,((2*b.z)/50))
        t.animate_z(.5,duration=((24*15)/25),curve=curve.linear)
        destroy(t,((25*15)/25)+3)
        Sequence(((25*15)/25)+3,Func(self.ask_input_fields)).start()
    
    class RocketController(Entity):
        TOP_SPEED_MPS=300
        TOP_SPEED_KMPH=1080
        
        MPH_CONST=1.609344
        TOP_SPEED_MPH=round(TOP_SPEED_KMPH/MPH_CONST)
        MPS_CONST=1000/3600
        def __init__(self,first_person_controller:FirstPersonController,inst,**kwargs):
            self.speedometer = inst()
            self.speedkph=0
            self.speedmph=0
            self.speedmps=0
            self.air_time=0
            self._activated=False
            self.controller=first_person_controller
            self.sky:Entity=None
            self.all_planets=[]
            self.original_speed=self.controller.speed
            super().__init__(model="stylized_spaceship.obj",texture=load_texture("stylized_spaceship.png"),**kwargs)

        @property
        def activated(self):
            return self._activated
        @activated.setter
        def activated(self, value):
            self._activated = value
            if value == True:
                self.controller.speed=0
                camera.parent=self
                camera.x=-10
                self.controller.parent = self
            else:
                self.controller.speed=100
                camera.parent=self.controller.camera_pivot
                camera.x = 0
                self.controller.parent=scene
            self.controller.gravity=value
        def kmph2mps(self,kmph:int):
            return kmph*self.MPS_CONST
        def kmph2mph(self,kmph:int):
            return kmph/self.MPH_CONST
        def input(self,key):
            if distance_xz(self.world_position,self.controller.world_position) <30:
                if self.activated == False:
                    print_on_screen("press f to fly")
                else:
                    print_on_screen("press f to stop flying")
                if key=="f":
                    if self.activated==False:
                        self.activated=True
                    else:
                        self.activated=False
        def update(self):
            if self.activated:
                self.rotation_y += mouse.velocity[0] * 40

                self.rotation_x -= mouse.velocity[1] * 40
                self.rotation_x= clamp(self.rotation_x, -90, 90)
                if held_keys["w"]:
                    if self.speedkph<self.TOP_SPEED_KMPH:
                        self.speedkph+=2
                if held_keys["s"]:
                    if self.speedkph>0:
                        self.speedkph-=2
                if not held_keys["w"]:
                    if self.speedkph>0:
                        self.speedkph-=1
                self.speedmph = round(self.kmph2mph(self.speedkph))
                self.speedmps = self.kmph2mps(self.speedkph)
                self.speedometer.val=self.speedkph
                
                self.direction = self.forward*self.speedkph
                origin = self.world_position + (self.up*.5)
                hit_info = raycast(origin , self.direction, ignore=(self,), distance=.5, debug=False)
                if not hit_info.hit:
                    self.position += (self.direction/100)
                if distance(Vec3(),self) <=1000:
                    self.sky.alpha=lerp(255,0,distance(Vec3(),self)/1000)
                else:
                    self.sky.alpha=125
    def worley_noise(self,resolution=16):
        t = Texture("white.png")
        pts = []
        for _ in range(resolution):
            x,y = random.randrange(0,t.width),random.randrange(0,t.height)
            if t.get_pixel(x,y)==color.black:
                continue
            else:
                t.set_pixel(x,y,color.black)
                pts.append((x,y))
                t.apply()
        
        for v in range(t.width):
            for j in range(t.height):
                distances = []
                for i in pts[:]:
                    distances.append(distance2d((v,j),i))
                b = sorted(distances)
                noise = b[0]
                t.set_pixel(v,j,self.ind_color(noise,noise,noise,b[len(b)-1],noise).invert())
                t.apply()
        return t
    def worley_noise_as_list(self,size=Vec2(20,20),resolution=16):
        w,h=size
        
        pts = []
        vals = []
        for _ in range(resolution):
            x,y = random.randrange(0,w),random.randrange(0,h)
            if (x,y) in pts:
               continue
            else:
                pts.append((x,y))
        
        for v in range(w):
            for j in range(h):
                distances = []
                for i in pts[:]:
                    distances.append(distance2d((v,j),i))
                b = sorted(distances)
                noise = b[0]
                vals.append(noise)
        return vals
    class Planet(Button):
        def __init__(self,**kwargs):
            super().__init__(b=kwargs["b"])
            del kwargs["b"]
            self.no_visible_entity = Entity()
            self.parent=self.no_visible_entity
            self.time_period=250
            self.all_planets=[]
            
            for key,value in kwargs.items():
                setattr(self,key,value)
            self.collider="mesh"
            
            self.orbit()

        def gravity(self):
            for body in self.all_planets:
                if body != self:
                    sqrdst=self.sqr_mag_of_vec(body.position+self.position)

        def sqr_mag_of_vec(self,vec:Vec3):
            return Vec3(*vec.dot(vec))
        def orbit(self):
            self.no_visible_entity.animate_rotation_x(360,duration=self.time_period,curve=curve.linear,loop=True)
            self.animate_rotation_x(-360,duration=self.time_period,curve=curve.linear,loop=True)
    def draw_board(self):
        all_planets = []
        
        self.t = Tk()
        self.btn=Progressbar()
        self.btn.pack()
        t = self.mstime
        b = self.btn
        Entity = self.Entity

        for obj in self.objs:
            p = self.Planet(b=b,model=obj,y=(self.objs.index(obj)+1)*5000,scale=1000,double_sided=True,shader=basic_lighting_shader,all_planets=all_planets)
            all_planets.append(p)
            if obj.find("Planet")!=-1:
                p.texture="PlanetTexture"
            elif obj.find("Asteroid")!=-1:
                p.color="#404040"
            elif obj.find("Moon")!=-1:
                p.texture="MoonTexture"
        m = Entity(b=b,parent=camera.ui, model="quad", texture="border_texture", scale=(.5,.5),position=(-.5,-.25))
        self.m_player = Entity(b=b,parent=m,model='sphere',color=color.red,position=0,scale=self.mscale(25,25))
        Entity(b=b,model='cube',parent=self.m_player,scale = (.25,1),position = (0,.5),color=color.red)
        for i in self.rangelen(self.inp_list):
            li1 = self.inp_list[i]
            li2 = self.inp_val_list[i]
            for inp in li1[:]:
                li2.append(inp.text)
            for inp in self.combined_inps[:]:
                inp.enabled = False
        self.v1 = True
        self.r = self.Rainbow(b=b,parent=scene,Arc=self.Arc,scale=1000)
        freq = 10
        for i in range(freq):
            self.clouds.append(self.Cloud(.5,50,x=-5000,y=500,z=random.randrange(-500,500),scale=250,b=b,model='sphere'))
        s = Entity(b=b,model=Cone(resolution=75,add_bottom=False,height=.5),scale=200,collider="mesh",position=(30,60,30),rotation=(0,0,180),double_sided=True)
        l = Entity(b=b,parent=s,model=Cylinder(),scale=(.005,1,.005),color=color.yellow,position=(.5,0,0))
        l1 = Entity(b=b,parent=s,model=Cylinder(),scale=(.005,1,.005),color=color.yellow,position=(.49,0,.01))
        self.lift = Entity(b=b,parent=scene,model="cube",x=lerp(l.world_x,l1.world_x,.5)+.05,y=0,z=lerp(0,l1.world_z,.5),scale=20,collider="box",color=color.yellow,double_sided=True)
        Entity(b=b,parent=self.lift,model="plane",y=-.5,collider="box",scale=Vec2(1,1)) 
        self.txt = Text(text="creating cubes for game...", color=color.white, position=(-.3, 0))
        self.bgm_audio.stop()
        self.q = Entity(b=b,model="cube", scale=Vec3(1000, .1, 1000), color=color.hex("#404040"), collider="box",
                        shader=basic_lighting_shader)
        
       
        self.Hill(b=b,scale=500, position=(795, 0, 0), color=color.green, collider="sphere")
        for i in range(4):
            for j in range(4):
                e = Entity(b=b,parent=scene, model="sphere", scale=2, position=self.TOKENS_STARTING_VEC[i][j],
                           color=self.TOKEN_COLORS[i])
                self.vec_pathpoints[i][j].append(e.position)
                e.shader = basic_lighting_shader
                self.pieces[i].append(e)


        team_names = self.inp_val_list[0]
        p_list = self.combine_lists(self.inp_val_list[1:])
        for string in p_list[:]:
            self.add_player_name_to_storage(string)
        for string in team_names:
            self.add_team_name_to_storage(string)
        self.combined_inps = []
        self.b.enabled = False
        self.flag = self.Flag()
       
        self.player = FirstPersonController()
        self.rocket=self.RocketController(first_person_controller=self.player,inst=self.Speedometer,b=b,sky=self.sky,scale=10,x=-100,all_planets=all_planets)
        self.hbar = HealthBar()
        self.hbar.x = .25
        self.bl_entity = Entity(b=b,parent=camera.ui, model="cube", scale=(3, 3), color=color.rgb(0, 0, 0, 0))

        self.player.speed = 100
        buildings = []
        Entity(b=b,parent=scene, model="cube", scale=(4, 20, self.BOARD_SIDE), position=(-4, 0, self.BOARD_SIDE / 2 - 2),
               texture="border_texture", collider="box", shader=basic_lighting_shader)
        Entity(b=b,parent=scene, model="cube", scale=(self.BOARD_SIDE, 20, 4), position=(self.BOARD_SIDE / 2 - 2, 0, -4),
               texture="border_texture", collider="box", shader=basic_lighting_shader)
        Entity(b=b,parent=scene, model="cube", collider="box", scale=(self.BOARD_SIDE, 20, 4),
               position=(self.BOARD_SIDE / 2 - 2, 0, self.BOARD_SIDE),
               texture="border_texture", shader=basic_lighting_shader)
        Entity(b=b,parent=scene, model="cube", scale=(4, 20, self.BOARD_SIDE),
               position=(self.BOARD_SIDE, 0, self.BOARD_SIDE / 2 - 2),
               texture="border_texture", collider="box", shader=basic_lighting_shader)
        Entity(b=b,parent=scene, model="cube", color=color.brown, scale=(3, 4, .25), position=(self.BOARD_SIDE - 2.1,
                                                                                           4, self.BOARD_SIDE / 2 - 2),
               rotation=(0, 90, 0), shader=basic_lighting_shader)
        Entity(b=b,parent=scene, model="sphere", color=color.gold, scale=.5, position=(self.BOARD_SIDE - 2.375,
                                                                                   4, self.BOARD_SIDE / 2 - 1),
               rotation=(0, 90, 0), shader=basic_lighting_shader)
        self.broken_center_coords = self.Coords(self.mid(15), self.mid(15)).break_dict()
        x = self.broken_center_coords["x"]
        z = self.broken_center_coords["z"]
        self.c_coords = [[], [], [], []]
        self.values = [[x + 1, x + 1, x + 1, x + 1, x + 1, x + 1], [x - 1, x - 1, x - 1, x - 1, x - 1, x - 1],
                       [x - 1, x - 1, x - 1, x - 1, x - 1, x - 1], [x + 1, x + 1, x + 1, x + 1, x + 1, x + 1]]
        for j in range(4):
            obj = self.values[j]
            for i in self.rangelen(obj):
                if j == 1 or j == 2:
                    obj[i] -= i
                elif j == 0 or j == 3:
                    obj[i] += i
        for i in self.rangelen(self.values):
            obj = self.values[i]
            o = self.ORDER_LIST[i]
            for num in obj[:]:
                if self.ORDER[o] == "x":
                    self.c_coords[i].append(self.Coords(num, z))
                elif self.ORDER[o] == "z":
                    self.c_coords[i].append(self.Coords(x, num))

        for i in range(-5, 5):
            for j in range(-5, 5):
                if not((i < 2) and (i>-2)) or not((j < 2)and j>-2):
                    e = Entity(b=b,parent=scene, model="cube", position=Vec3(i * (1000 / 8), 0, j * (1000 / 8)),
                           color=random.choice(self.URSINA_COLORS_LIST),
                           scale=Vec3(50, random.randrange(self.BOARD_SIDE * 2, 1000), 50),collider="box",shader = basic_lighting_shader)
                    Entity(b=b,parent=m, model="cube", position=self.mpos(i * (1000 / 8), j * (1000 / 8)),
                           scale=self.mscale(50,50),
                           color=e.color)
                    buildings.append((e.position,e.scale))
        for i in range(15):
            for j in range(15):
                
                e = Entity(b=b,parent=scene, model="cube", scale=4, collider="box", texture="border_texture",
                           shader=basic_lighting_shader, color=color.rgb(255, 255, 255), position=(i * 4, 0, j * 4))
                self.l_enties.append(e)
                for c in self.rangelen(self.c_coords):
                    obj = self.c_coords[c]
                    for coords in obj[:]:
                        if self.Coords(i, j) == coords:
                            e.color = self.COLORS[c]
                for index in range(len(self.SAFE_MODE_COORDS["red"])):
                    if ((i == 5 and j <= 5) or (j == 5 and i <= 5)) and j != 1:
                        e.scale_y = 20
                    if (((((i == 5 and j <= 14) and j >= 14 - 5) or (j == 14 - 5 and i <= 5)) and i != 1)):
                        e.scale_y = 20
                    if (((((j == 5 and i <= 14) and i >= 14 - 5) or (i == 14 - 5 and j <= 5)) and i != 13)):
                        e.scale_y = 20
                    if (((j == 14 - 5 and i <= 14) and i >= 14 - 5) or (
                            (i == 14 - 5 and j <= 14) and j >= 14 - 5)) and j != 14 - 1:
                        e.scale_y = 20
                    if i < 5 and j < 5:
                        e.color = color.red
                        e.texture = None
                    if i > 14 - 5 and j < 5:
                        e.color = color.cyan
                        e.texture = None
                    if i < 5 and j > 14 - 5:
                        e.color = color.green
                        e.texture = None
                    if i > 14 - 5 and j > 14 - 5:
                        e.color = color.yellow
                        e.texture = None

                    if Vec3(i, 0, j) == self.SAFE_MODE_COORDS["green"][index]:
                        self.safePositions.append(e)
                        e.color = color.red
                        e.texture = None
                    if Vec3(i, 0, j) == self.SAFE_MODE_COORDS["blue"][index]:
                        self.safePositions.append(e)
                        e.color = color.cyan
                        e.texture = None
                    if Vec3(i, 0, j) == self.SAFE_MODE_COORDS["red"][index]:
                        self.safePositions.append(e)
                        e.color = color.green
                        e.texture = None
                    if Vec3(i, 0, j) == self.SAFE_MODE_COORDS["yellow"][index]:
                        self.safePositions.append(e)
                        e.color = color.yellow
                        e.texture = None
                if not ((i < 6 and j < 6) or (i > 14 - 6 and j < 6) or (i < 6 and j > 14 - 6) or (
                        i > 14 - 6 and j > 14 - 6)):
                    Text(parent=scene,text=str(self.index),position=(e.x,2,e.y),scale=2,color=color.black,double_sided=True)
                    self.pathPoints.append(e)
                    self.index += 1
        self.sun = Entity(b=b,parent=self.sky, y=.5, scale=1000, shadows=True, color=color.white)
        self.moon = Entity(b=b,parent=self.sky,y=-.5, scale=1000, shadows=True,
                                     color=color.rgba(255, 255, 255, 25))
        self.tablet = self.UiTablet(self.combineCaptureFtTime,self.switch,self.inp_val_list,self.turn)
        for i in range(250):
            e1 = Entity(b=b,parent=scene,model="cube",scale = Vec3(2,5,2),position=Vec3(random.randrange(-500,500,6),2.5,random.randrange(-500,500,6)),
                   color=random.choice(self.URSINA_COLORS_LIST),shader=basic_lighting_shader)
            #self.seqs.append(e1.animate_position(value=self.rpos,duration=10,curve=curve.linear))
            e1.animate_position(self.lift.position,duration=20,curve=curve.linear)
            self.p.append(e1)
        self.entity_index_pathpoints = {
            "yellow":self.remove_duplicates(
            self.range(61, 56, -1)
            + self.range(65, 80, 3)
            + [79, 78] +
            self.range(78, 60, -3) +
            self.range(54, 48, -1) +
            self.range(48, 18, -15) +
            self.range(18, 24) +
            self.range(15, 0, -3) +
            [1] +
            self.range(2, 18, 3) +
            self.range(26, 32) +
            self.range(47, 40, -1)),

            
            "blue":self.remove_duplicates(self.range(75,63,-3)+
            self.range(54, 48, -1) +
            self.range(48, 18, -15) +
            self.range(18, 24) +
            self.range(15, 0, -3) +
            [1] +
            self.range(2, 18, 3) +
            self.range(26, 32) +
            self.range(32,62,15)+
            self.range(61, 56, -1)
            + self.range(65, 80, 3)+
            self.range(79,64,-3)+
            [55,40]),

            
            "red":self.remove_duplicates(self.range(19,24)+
            self.range(15, 0, -3) +
            [1] +
            self.range(2, 18, 3) +
            self.range(26, 32) +
            self.range(32,62,15)+
            self.range(61, 56, -1)
            + self.range(65, 80, 3)+
            self.range(80,78,-1)+
            self.range(75,63,-3)+
            self.range(54, 48, -1) +
            self.range(33,40)),
            
            
            "green":self.remove_duplicates(self.range(5,17,3)+
            self.range(26, 32) +
            self.range(32,62,15)+
            self.range(61, 56, -1)
            + self.range(65, 80, 3)+
            self.range(80,78,-1)+
            self.range(75,63,-3)+
            self.range(54, 48, -1) +
            [33,18]+
            self.range(19,24)+
            self.range(15, 0, -3) +
            [1] +
            self.range(1, 16, 3) +
            [25,40])
        }
        for i in range(4):
            self.entity_pathpoints[i] = [self.pathPoints[j] for j in self.entity_index_pathpoints[self.GAME_ORDER_LIST[i]]]
            
            print(len(self.entity_pathpoints[i]))
        

        self.txt.enabled = False
        t2 = self.getloadtime(t)
        self.t.destroy()
        self.GameNotification(text=f"created {len(scene.entities)} objects in :-{t2}ms\ncreated 1 object in {round(t2/len(scene.entities),3)}ms",timeout=100,color=color.black)
        self.t = self.Timer(self.end_func)
        self.timestamp = self.TimeStamp(position=(0,.45))
        self.drawen_board = True
    def ind_color(self,b,c,d,m,a=255):
        if m == 1:
            return Color(b,c,d,a/255)
        else:
            return Color(b/m,c/m,d/m,a/m)
    
    def end_func(self):
        self.switch(1)
    @property
    def mstime(self):
        return int(time.time() * 1000)
    def getloadtime(self,t1):
        return self.mstime - t1
    @property
    def rpos(self):
        return Vec3(random.randrange(-500,500),2.5,random.randrange(-500,500))
    def is_seq_complete(self,s:tuple[Sequence]):
        i = 0
        l = 0
        for seq in s[:]:
            i+=1
            if seq.finished:
                l+=1
        return i == l
    def collision(self,e1:Entity,boxscale:Vec3,boxpos:Vec3=Vec3(0,0,0)):
        i = 0
        axes = ["x","y","z"]
        for val in axes[:]:
            v1 = getattr(e1.position,val)
            v2 = getattr(boxscale,val)
            v3 = getattr(boxpos,val)
            if ((v1 > (v3 - v2/2)) or (v1 < (v3 + v2/2))):
                i+=1
            else:
                pass
        return i == len(axes)



    def remove_duplicates(self,li):
        return list(dict.fromkeys(li))
    def range(self, *p) -> list[int]:
        l: list[int]
        try:
            if abs(p[2]) != p[2]:
                l = list(range(p[0], p[1] - 1, p[2]))
            else:
                l = list(range(p[0], p[1] + 1, p[2]))
        except IndexError:
            try:
                l = list(range(p[0], p[1] + 1))
            except IndexError:
                l = list(range(p[0] + 1))

        return l

    def rangelen(self, expr):
        return range(len(expr))

    def dict_to_coords(self, dict: dict[str, int]):
        [x, z] = dict
        return self.Coords(x, z)

    @property
    def time_in_one_day(self):
        return 60 * 60 * 60 * 24

    def combine_lists(self, list: list[list]):
        l = []
        for obj in list[:]:
            for val in obj[:]:
                l.append(val)
        return l

    def mid(self, num):
        if num / 2 != ceil(num / 2):
            return (num / 2) + 0.5
        else:
            raise TypeError("Number given is not odd")

    def inp(self, key):
        self.fps.input(key)
        if self.drawen_board:
            if key == 'r':
                self.hbar.value = 100
            if key == "q":
                application.quit()
            if key == "h":
                self.tablet.switch_program(del_pg_name=self.tablet.current_program, create_pg_name="help.exe")
            elif key == "m":
                self.tablet.switch_program(del_pg_name=self.tablet.current_program, create_pg_name="minimap.exe")
            elif key == "c":
                self.tablet.switch_program(del_pg_name=self.tablet.current_program, create_pg_name="console.exe")
            if self.tablet.current_program == "console.exe":
                if key == "up arrow":
                    self.tablet.highlight_index -= 1
                elif key == "down arrow":
                    self.tablet.highlight_index += 1
                if key == "enter" and len(self.tablet.suggestions) == 0:
                    self.tablet.switch_program(del_pg_name=self.tablet.current_program,
                                               create_pg_name=self.tablet.console_text_entity.text.replace("run ", ''))
                if key == "enter":
                    self.tablet.console_text_entity.text += self.tablet.PG_NAME_LIST[
                        self.tablet.highlight_index % len(self.tablet.PG_NAME_LIST)]
                    for entity in self.tablet.suggestions:
                        destroy(entity)
                    self.tablet.suggestions = []

            if key == "r" and self.tablet.current_program == "dice_roll.exe":
                self.dice_roll()
            if key == "r" and self.tablet.current_program != "dice_roll.exe":
                self.tablet.switch_program(del_pg_name=self.tablet.current_program, create_pg_name="dice_roll.exe")
            if distance_xz(self.player,self.lift) < 30 and key=="a" and self.lift.y==0:
                self.go_up([])
            elif distance_xz(self.player,self.lift) < 30 and key=="a" and self.lift.y==50:
                self.go_down([self.player])
    def normalize(self,vec3): 
        distance = sqrt(vec3.x * vec3.x + vec3.y * vec3.y+vec3.z * vec3.z)
        return Vec3(vec3.x / distance, vec3.y / distance,vec3.z/distance)
    def lerp(self,a,b,t):
        return a + (b-a) * (1-cos(t*pi))/2
    
    
    def noise(self,x):
        x = x*.01 % 254;
        return self.lerp(self.perm[floor(x)], self.perm[ceil(x)], x - floor(x))

    def evaluate(self,pt:Vec3,octaves:int):
        p_name = "perlin_noise_"+str(octaves)
        if hasattr(self,p_name):
            p = getattr(self,p_name)
            return (p(coordinates=(pt.x+.5,pt.y+.5,pt.z+.5))+1)*.5
        else:
            setattr(self,p_name,PerlinNoise(octaves=octaves))
            p = getattr(self, p_name)
            return (p(coordinates=(pt.x+.5,pt.y+.5,pt.z+.5))+1)*.5
    
    #     dirs = [Vec3(0,.5,0),Vec3(0,-.5,0),Vec3(.5,0,0),Vec3(-.5,0,0),Vec3(0,0,.5),Vec3(0,0,-.5)]
    #     verts,tris = [],[]
    #     g = Entity(**kwargs)
    #     for i in dirs[:]:
    #         f = self.TerrainFace(i,res)
    #         Entity(parent=g,model=f)
    #     g.combine()
    #     return g
    # def TerrainFace(self,localup:Vec3,resolution=16):
    #     a1=Vec3(*(i for i in localup.yz), localup.x)
    #     a2 = localup*a1
    #     verts = [Vec3(resolution**2,resolution**2,resolution**2)]*(resolution**2)
    #     tris= [((resolution-1)**2)*6]*((resolution-1)**2)*6
    #     i = 0
    #     tri_index=0
    #     for y in range(resolution):
    #         for x in range(resolution):
    #             percent = Vec2(x,y)/resolution-1
    #             point_on_unit_cube = localup+(percent.x-.5)*2*a1*(percent.y-.5)*2*a2
    #             point_on_unit_sphere = self.normalize(point_on_unit_cube)
    #             verts[i]=point_on_unit_sphere
    #             if x!=resolution-1 and y!=resolution-1:
    #                 tris[tri_index]=i
    #                 tris[tri_index+1]=i+resolution+1
    #                 tris[tri_index+2]=i+resolution
    #                 tris[tri_index+3]=i
    #                 tris[tri_index+4]=i+1
    #                 tris[tri_index+5]=i+resolution+1
    #                 tri_index+=6
    #             i+=1
    #     return Mesh(vertices=verts,triangles=tris)
    
    @property
    def percentage_of_modules_used(self):
        l = []
        print(self.code)
        modules = [i[7:] for i in self.code.splitlines() if i.startswith("import")]
        secondary_modules = [i[5:i.find(".")]   if i.find(".") != -1 else i[5:i.find("import")-1] for i in self.code.splitlines() if i.startswith("from")]
        secondary_modules_content = [i[i.find("import")+1:] for i in self.code.splitlines() if i.startswith("from")]
        import builtins
        l=[b for i in dir(builtins) for j in dir(i) for b in dir(j) if not i.startswith('__') and not j.startswith('__')]
        percentages={}
        _chars = dict.fromkeys(modules+secondary_modules)
        for i in modules:
            _chars[i]=0
            for b in dir(eval(i)):
                if not b.startswith('__')and b in self.code:
                    _chars[i]+=self.code.count(b)*len(b)
        _chars["builtins"]=0
        for b in dir(builtins):
            if not b.startswith('__')and b in self.code:
                _chars["builtins"]+=self.code.count(b)*len(b)            
        for i in self.rangelen(secondary_modules):
            
            try:
                _chars[secondary_modules[i]]=0
                if secondary_modules_content[i] != "*":
                    for b in secondary_modules_content[i].split(","):
                        
                        if not b.startswith('__') and b in self.code:
                            _chars[secondary_modules[i]]+=(self.code.count(b)*len(b))             
                else:
                    exec(f"""import {secondary_modules[i]}""")
                    for b in dir(eval(secondary_modules[i])):
                        
                        if not(b.startswith('__')) and b in self.code:
                            _chars[secondary_modules[i]]+=(self.code.count(b)*len(b))
            except: 
                pass
        # keys = []
        # for key, value in _chars.items():
        #     if key not in keys:
        #         for k,v in _chars.items():
        #             if k.startswith(key):
        #                 _chars[key]+=v
        #                 keys.append(k)
        #             else:
        #                 pass
        #     else:
        #         pass
        # _keys = self.remove_duplicates(keys)
        # for key in _keys:
        #     del _chars[key]
        # del keys
        return _chars

    def read_pos(self, string):
        return Vec3(*eval(string[4:]))

    def make_pos(self, vec3: Vec3):
        return str(vec3)

    def update(self):
        if self.asked_input_fields:
            self.sky.rotation_x += .05 / (held_keys["g"] + 1)
        self.fps.loop()
        
        if self.drawen_board:

            for c in self.clouds:
                if c.x < 5000:
                    c.x+=10
                else:
                    c.x=-5000
            
            if distance_xz(self.player,self.lift)<30:
                print_on_screen("press a key to go in lift",duration=1)
            if not self.player.grounded and not held_keys["t"] and not self.player.jumping and self.j==1:
                self.at = self.player.y
                self.j = 0
            if self.player.grounded and self.at >=10 and self.j==0:
                self.hbar.value -= self.at-10
                self.j=1
            self.timestamp.update()
            if self.t.finished and not self.is_transition_in_process and self.is_stuck_to_player:
                self.keep_player_with_token(self.switch_index)
            self.tablet.h.color =[color.cyan,color.red,color.green,color.yellow][self.turn]
            self.m_player.position = self.mpos(self.player.x,self.player.z)
            self.m_player.rotation_z = self.player.rotation_y
            if self.tablet.current_program == 'minimap.exe':
                for t in range(16):
                    [x,_,z] = self.combine_lists(self.pieces)[t].position
                    pos = self.tablet.minimap_Vec(x,z)
                    self.combine_lists(self.tablet.pieces)[t].position = pos
            # self.pieces[0][0].position = self.player.position
            # if self.i <60*10:
            #    self.i+=1
            # else:
            #    self.pieces[0][1].position = self.read_pos(self.n.send(self.make_pos(self.p).encode("utf-8")))
            #for i in range(250):
            #    seq = self.seqs[i]
            #    e = self.p[i]
            #    if self.is_seq_complete(seq):
            #        self.replace(self.seqs,seq,e.animate_position(value=self.rpos,duration=10,curve=curve.linear))
            if held_keys[Keys.down_arrow] and self.tablet.current_program == "credits.exe":
                self.tablet.e.y += .01
            if held_keys[Keys.up_arrow] and self.tablet.current_program == 'credits.exe':
                self.tablet.e.y -= .01
            for i in self.rangelen(self.tablet.suggestions):

                if i == self.tablet.highlight_index % len(self.tablet.PG_NAME_LIST):
                    self.tablet.suggestions[i].color = color.blue
                else:
                    self.tablet.suggestions[i].color = color.white
            if held_keys[Keys.down_arrow] and self.tablet.current_program == "dice_roll.exe":
                self.tablet.dice.rotation_x-=1
            if held_keys[Keys.up_arrow] and self.tablet.current_program == "dice_roll.exe":
                self.tablet.dice.rotation_x+=1
            if held_keys[Keys.left_arrow] and self.tablet.current_program == "dice_roll.exe":
                self.tablet.dice.rotation_y+=1
            if held_keys[Keys.right_arrow] and self.tablet.current_program == "dice_roll.exe":
                self.tablet.dice.rotation_y-=1
            
            
            # if self.player.world_y < 0:
                
            #         self.b_entity.visible = True
            # else:
            #     self.b_entity.visible = False
            self.time = round((self.sky.rotation_x / 360) * 86400)
            
            self.btry = psutil.sensors_battery().percent
            self.tablet.txt.text = self.combineCaptureFtTime(self.time) + " " + str(self.btry) + "%"
            if self.flag.f_index < 75:
                self.flag.f_index += 1
            else:
                self.flag.f_index = 25
            self.rot = 90 + self.sky.rotation_x

            # self.sun.rotation_x += .05 / (held_keys["g"] + 1)
            # self.moon.rotation_x += .05 / (held_keys["g"] + 1)
            # if self.player.y <= -900:
            #     self.player.y = 100
            self.t.loop()

p = Program()
i = 0
p.code = inspect.getsource(sys.modules[__name__])
def update():
    
    p.update()


def input(key):
    p.inp(key)


p.run()
