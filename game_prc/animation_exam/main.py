from ursina import *
from player import Player
from sword import *
from enemy import Enemy

app = Ursina()

player = Player("cube", (0, 10, 0), "box")
player.SPEED = 2
player.jump_height = 0.3

scene.player = player
enemies = [Enemy(x=x*4) for x in range(4)]


ground = Entity(model = "cube", scale = (100, 1, 100), collider = "box", color = color.light_gray, texture = "white_cube")

PointLight(parent = camera, color = color.white, position = (0, 10, -1.5))
AmbientLight(color = color.rgba(100, 100, 100, 0.1))

Sky()

sword = Sword()

def input(key):
    if key == "left mouse down":
        sword.resume()
        invoke(sword.pause, delay=1.4)
        for e in enemies:
            if distance(player.position, e.position) < 3:
                e.take_damage(10)


app.run()