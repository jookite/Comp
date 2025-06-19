from ursina import *

class Sword(FrameAnimation3d):
    def __init__(self, position = (1.5, -2.2, 1.8), rotation = (0, 90, 0)):
        super().__init__(
            "sword_",
            fps= 100,
            frame_times= 200,
            autoplay= True,
            loop= True,
            position = position,
            rotation = rotation,
            scale = (4, 4, 4),
            texture = "sword",
            parent = camera
        )
        self.pause()
