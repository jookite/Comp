from ursina import *
from ursina.shaders import lit_with_shadows_shader


Entity.default_shader = lit_with_shadows_shader

shootables_parent = Entity()

class Enemy(Entity):
    def __init__(self, position=(0, 0, 5), speed=1, max_hp=30, **kwargs):
        super().__init__(
            parent=shootables_parent,
            model='cube',
            color=color.red,
            scale=(1.5, 8, 1.5),
            position=position,
            origin_y=0,
            collider='box',
            **kwargs
        )
        self.speed = speed
        self.max_hp = max_hp
        self.hp = max_hp
        self.is_dead = False
        # self.health_bar = Entity(
        #     parent=self,
        #     model='cube',
        #     color=color.green,
        #     world_scale=(1.3, 0.1, 0.1),
        #     y=self.scale_y + 0.2
        # )
        self.health_bar = Entity(
            parent=self,
            y=1.2,
            model='cube',
            color=color.green,
            world_scale=(1.5,.1,.1)
        )


def update(self):
    if self.is_dead:
        return

    if hasattr(scene, 'player'):
        direction = scene.player.position - self.position
        direction.y = 0
        distance_to_player = direction.length()

        if distance_to_player > 1:
            self.position += direction.normalized() * time.dt * self.speed

    def take_damage(self, amount):
        self.hp -= amount
        self.health_bar.scale_x = max(0.01, self.hp / self.max_hp * 1.3)
        self.health_bar.color = color.red if self.hp < self.max_hp / 2 else color.green

        if self.hp <= 0:
            self.die()

    def die(self):
        self.is_dead = True
        destroy(self)
