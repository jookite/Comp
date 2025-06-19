# =============================================================
# 0) IMPORT 및 전역 상수 정의
# =============================================================
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.prefabs.ursfx import ursfx
from ursina.shaders import lit_with_shadows_shader
import random, time, math

# ---------- 게임 전역 상수 ----------
EPS             = 0.001        # 스케일이 0이 되는 일을 방지 (UI 막대 등)
MAX_AMMO        = 10           # 한 번 장전 시 얻는 탄약 수
TOTAL_ROUNDS    = 5            # 총 라운드 수
BASE_ENEMIES    = 8            # 1라운드 적 기본 수
INC_PER_ROUND   = 4            # 라운드마다 늘어나는 적 수

# =============================================================
# 1) 기본 설정
# =============================================================
app = Ursina()
random.seed(0)
Entity.default_shader = lit_with_shadows_shader
window.color = color.rgb(10, 10, 10)

# =============================================================
# 2) 월드 오브젝트 : 지면 · 플레이어 · 총기
# =============================================================
ground = Entity(
    model='plane', collider='box', scale=64,
    texture='grass', texture_scale=(4, 4)
)

editor_camera = EditorCamera(enabled=False, ignore_paused=True)

# ---------- 플레이어 ----------
player = FirstPersonController(
    model='cube', color=color.orange, origin_y=-.5,
    speed=8, collider='box', z=-10
)
player.collider = BoxCollider(player, Vec3(0, 1, 0), Vec3(1, 2, 1))

# ---------- 무기 ----------
gun = Entity(
    model='cube', parent=camera, position=(.5, -.25, .25),
    scale=(.3, .2, 1), origin_z=-.5, color=color.red,
    on_cooldown=False
)
gun.muzzle_flash = Entity(
    parent=gun, model='quad', world_scale=.5, z=1,
    color=color.yellow, enabled=False
)

# ---------- 적을 담을 부모 노드 ----------
shootables_parent = Entity()
mouse.traverse_target = shootables_parent

# =============================================================
# 3) UI
# =============================================================
ui_root = Entity(parent=camera.ui)

# 체력바
hp_bar = Entity(
    parent=ui_root, model='quad', color=color.lime,
    scale=(.30, .03), origin=(-.5, 0), position=(-.62, -.47), z=-.01
)
hp_text = Text(
    parent=ui_root, scale=.7, origin=(-.5, 0), position=(-.46, -.49)
)

# 탄약 & 재장전 바
ammo_text = Text(
    parent=ui_root, scale=.7, origin=(.5, 0), position=(.62, -.49)
)
reload_bar = Entity(
    parent=ui_root, model='quad', color=color.azure,
    scale=(EPS, .03), origin=(.5, 0), position=(.62, -.47), z=-.01
)

# 라운드 표시
round_text = Text(
    'Round 1 / 5', parent=ui_root, scale=1.5,
    origin=(0, 0), position=(0, .45), color=color.yellow
)

# 게임 오버 화면
game_over_text = Text(
    'GAME OVER', parent=ui_root, scale=3,
    origin=(0, 0), enabled=False, color=color.red
)
restart_button = Button(
    text='Restart  (R)', parent=game_over_text,
    color=color.azure, scale=.15, origin=(0, 0), y=-.1,
    enabled=False
)

# 일시정지 패널
pause_panel = WindowPanel(
    title='PAUSED (Tab 재개)', content=(),
    enabled=False, parent=ui_root, scale=.5
)

# =============================================================
# 4) 전역 상태 변수 및 초기화 함수
# =============================================================
current_round = 1
ammo          = MAX_AMMO
reloading     = False

def reset_state() -> None:
    '''게임을 초기 상태(1라운드)로 리셋'''
    global current_round, ammo, reloading, shootables_parent

    # 1) 플레이어 상태 초기화
    player.position = Vec3(0, 0, -10)
    player.hp = player.max_hp = 100

    # 2) 라운드·탄약·재장전 상태 초기화
    current_round = 1
    ammo, reloading = MAX_AMMO, False
    round_text.text = f'Round {current_round} / {TOTAL_ROUNDS}'
    reload_bar.scale_x = EPS

    # 3) 적 모두 제거 후 부모 노드 재생성
    destroy(shootables_parent)
    shootables_parent = Entity()
    mouse.traverse_target = shootables_parent

    # 4) UI 업데이트
    update_hp_ui()
    update_ammo_ui()
    game_over_text.enabled = restart_button.enabled = False
    game_over_text.text = 'GAME OVER'

    # 5) 라운드 시작
    start_round()

    # 6) 게임 흐름 제어
    application.paused = False
    mouse.locked = True

# =============================================================
# 5) UI 업데이트 함수
# =============================================================
def update_hp_ui() -> None:
    """플레이어 체력 UI를 최신 상태로 갱신"""
    ratio = max(0, player.hp / player.max_hp)
    hp_bar.scale_x = max(ratio * .30, EPS)
    hp_text.text   = f'{player.hp:>3} / {player.max_hp}'

def update_ammo_ui() -> None:
    """탄약 UI를 최신 상태로 갱신한다"""
    ammo_text.text = f'{ammo:>2} / {MAX_AMMO}'

# =============================================================
# 6) 총기(발사·재장전) 로직
# =============================================================
def reload() -> None:
    """재장전 시작"""
    global reloading
    if reloading:               # 이미 재장전 중이면 무시
        return

    reloading = True
    reload_bar.scale_x = EPS
    reload_bar.animate_scale_x(.28, duration=2, curve=curve.linear)
    ammo_text.text = 'Reloading…'
    invoke(finish_reload, delay=2)   # 2초 뒤 재장전 완료

def finish_reload() -> None:
    """재장전 완료"""
    global ammo, reloading
    ammo, reloading = MAX_AMMO, False
    reload_bar.scale_x = EPS
    update_ammo_ui()

def shoot() -> None:
    """마우스 왼쪽 버튼: 탄 발사"""
    global ammo
    if reloading or ammo <= 0 or gun.on_cooldown:
        return

    # 발사 연출
    gun.on_cooldown = True
    gun.muzzle_flash.enabled = True
    ursfx(
        # 단순 총소리 효과음
        [(0, 0), (0.1, 0.9), (0.15, 0.75), (0.3, 0.14), (0.6, 0)],
        volume=0.5, wave='noise',
        pitch=random.uniform(-13, -12), pitch_change=-12, speed=3
    )

    # 탄약 소모 및 UI 반영
    ammo -= 1
    update_ammo_ui()

    # 총구 화염·쿨타임 종료 예약
    invoke(gun.muzzle_flash.disable, delay=.05)
    invoke(setattr, gun, 'on_cooldown', False, delay=.15)

    # 피격 판정
    if mouse.hovered_entity and isinstance(mouse.hovered_entity, Enemy):
        target = mouse.hovered_entity
        target.take_damage(15)
        target.blink(color.red)

    # 탄약이 0이 되면 자동 재장전
    if ammo <= 0:
        reload()

# =============================================================
# 7) Enemy 클래스
# =============================================================
class Enemy(Entity):
    """플레이어를 추적·공격하는 기본 적 유닛"""

    def __init__(self, **kwargs):
        super().__init__(
            parent=shootables_parent, model='cube', color=color.light_gray,
            collider='box', scale_y=2, origin_y=-.5, **kwargs
        )

        # 스탯 설정
        self.max_hp      = random.randint(80, 120)
        self.hp          = self.max_hp
        self.speed       = random.uniform(4, 6)
        self.attack_pow  = random.randint(6, 10)
        self.last_attack = 0.0
        self.alive       = True

        # 체력바
        self.hp_bar = Entity(
            parent=self, model='cube', color=color.red, y=1.2,
            world_scale=(1.5, .1, .1), alpha=1
        )

    # ---------------------------------------------------------
    # 기본 update : 프레임마다 호출
    # ---------------------------------------------------------
    def update(self):
        if application.paused or not self.alive:
            return

        # 1) 플레이어와 거리/방향 계산
        dist = distance_xz(player.position, self.position)
        if dist > 40:            # 일정 거리 이상이면 추적 안함
            return

        self.look_at_2d(player.position, 'y')

        # 체력바 천천히 투명화
        self.hp_bar.alpha = max(0, self.hp_bar.alpha - time.dt)

        # 2) 레이캐스트로 시야 체크 후 이동·공격
        hit = raycast(
            self.world_position + Vec3(0, 1, 0),
            self.forward, 30, ignore=(self,)
        )

        # 플레이어가 시야 안에 있으면
        if hit.entity == player:
            if dist > 2:
                # 이동
                self.position += self.forward * self.speed * time.dt
            elif time.time() - self.last_attack > 1:   # 공격 간 쿨타임 1초
                self.last_attack = time.time()
                player.hp -= self.attack_pow
                update_hp_ui()

    # ---------------------------------------------------------
    # 데미지·사망 처리
    # ---------------------------------------------------------
    def take_damage(self, dmg: int) -> None:
        """피격 시 호출"""
        self.hp -= dmg
        if self.hp <= 0:
            self.die()
            return

        # 체력바 반영 및 잠깐 표시
        self.hp_bar.world_scale_x = max(0.01, self.hp / self.max_hp * 1.5)
        self.hp_bar.alpha = 1

    def die(self) -> None:
        '''적 사망 처리'''
        self.alive = False
        destroy(self)
        check_round_clear()

# =============================================================
# 8) 라운드 관리
# =============================================================
def spawn_enemy(x: float = 0, z: float = 0) -> None:
    """지정 위치에 적 소환"""
    Enemy(x=x, z=z)

def start_round() -> None:
    '''current_round 값을 기준으로 적 소환'''
    spawn_cnt = BASE_ENEMIES + INC_PER_ROUND * (current_round - 1)
    for _ in range(spawn_cnt):
        angle_deg = random.uniform(0, 360)
        radius    = random.uniform(4, 20)
        spawn_enemy(
            x=math.cos(math.radians(angle_deg)) * radius,
            z=math.sin(math.radians(angle_deg)) * radius
        )
    round_text.text = f'Round {current_round} / {TOTAL_ROUNDS}'

def check_round_clear() -> None:
    """남은 적이 없으면 다음 라운드 시작 or 승리 처리"""
    global current_round

    alive_enemies = [
        e for e in shootables_parent.children if isinstance(e, Enemy)
    ]
    if alive_enemies:
        return

    if current_round < TOTAL_ROUNDS:
        current_round += 1
        start_round()
    else:
        # ---------- 게임 승리 ----------
        game_over_text.text = 'YOU WIN'
        game_over_text.enabled = restart_button.enabled = True
        application.paused = True
        mouse.locked = False

# =============================================================
# 9) 메인 update 루프
# =============================================================
def update():
    # 사격
    if held_keys['left mouse'] and not application.paused:
        shoot()

    # 낙사 체크
    if player.y < -3 and not application.paused:
        trigger_game_over()

    # 플레이어 체력 체크
    if player.hp <= 0 and not application.paused:
        trigger_game_over()

def trigger_game_over() -> None:
    """게임 오버 처리"""
    game_over_text.text = 'GAME OVER'
    game_over_text.enabled = restart_button.enabled = True
    application.paused = True
    mouse.locked = False

# =============================================================
# 10) 입력 처리
# =============================================================
def handle_input(key):
    # Tab : 에디터 카메라 토글 + 일시정지
    if key == 'tab':
        editor_camera.enabled = not editor_camera.enabled
        application.paused    = editor_camera.enabled
        player.visible_self   = editor_camera.enabled
        gun.enabled           = not editor_camera.enabled
        pause_panel.enabled   = editor_camera.enabled
        mouse.locked          = not editor_camera.enabled
        if editor_camera.enabled:
            pause_panel.position = Vec2(0, 0)

    # R : 게임 오버/승리 화면에서 재시작
    if key == 'r' and application.paused:
        reset_state()

Entity(ignore_paused=True, input=handle_input)
restart_button.on_click = reset_state

# =============================================================
# 11) 라이팅 & 하늘
# =============================================================
sun = DirectionalLight()
sun.look_at(Vec3(1, -1, -1))
Sky()

# =============================================================
# 12) 메인
# =============================================================
if __name__ == '__main__':
    reset_state()   # 1라운드부터 시작
    app.run()
