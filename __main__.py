import abc
import pygame
import pygame.draw
import pygame.display as display
import pygame.event
import math
import time

assert not pygame.init()[-1], "初始化失败(pygame存在未初始化的模块)"
on_time: float = 10000  # 一次计算的时间间隔(沙盘时间)
world_time: float = 0.01  # 一个on_time等于实际的时间

UA = 149597870700
on_m: float = UA / 350  # 1UA的10分之一

G = 6.67 * (10 ** -11)  # 万有引力常数


class Planet(metaclass=abc.ABCMeta):
    def __init__(self):
        self.name = ""
        self.center: Planet = None
        self.x = 0
        self.y = 0

        self.r = 0  # 星球半径
        self.center_r = 0  # 距离中心天体的半径
        self.color = (0, 0, 0)
        self.m = 0

    def set_m(self, m: float):
        self.m = m

    def set_center_r(self, r: float) -> None:
        self.center_r = r

    def set_r(self, r: float) -> None:
        self.r = r

    def set_color(self, color: tuple) -> None:
        self.color = color

    @abc.abstractmethod
    def draw(self, dx, dy, max_x, max_y):  # dx和dy是偏移量
        pass

    def get_xy(self):  # dx和dy是偏移量
        return self.x, self.y

    def set_name(self, name) -> None:  # dx和dy是偏移量
        self.name = name

    def set_center(self, center) -> None:  # dx和dy是偏移量
        self.center: Planet = center

    def get_center_xy(self):  # dx和dy是偏移量
        return self.center.get_xy()

    def run(self):  # dx和dy是偏移量
        return self.get_xy()

    def get_name(self):  # dx和dy是偏移量
        return self.name

    def draw_name(self, dx, dy):
        pass


class Sun(Planet):
    def __init__(self):
        super(Sun, self).__init__()
        self.set_name("Sun")
        self.color = (255, 0, 0)

    def draw(self, dx, dy, max_x, max_y):  # dx和dy是偏移量
        dx = int(dx)
        dy = int(dy)
        if dx >= 0 and dy >= 0 and dx < max_x and dy < max_y:
            self.draw_name(dx, dy)
            r = int(self.r / on_m)
            pygame.draw.circle(screen, self.color, (dx, dy), r, 0)


class RunPlanet(Planet):
    def __init__(self):
        super(RunPlanet, self).__init__()
        self.sita = 0  # 与中心天体的角度
        self.v = 0  # 线速度
        self.v_type = 1  # 0-角速度，1-线速度

    def setting(self, center, m, r, color, center_r):
        self.set_center(center)
        self.set_color(color)
        self.set_r(r)
        self.set_m(m)
        self.set_center_r(center_r)
        v = math.sqrt(G * self.center.m / self.center_r)
        self.set_v(v, 1)

    def set_v(self, v: float, v_type: int = 1) -> None:
        self.v = v
        self.v_type = v_type

    def draw(self, dx=0, dy=0, max_x=0, max_y=0):  # dx和dy是偏移量
        self.run()
        x = int(self.x / on_m + dx)
        y = int(self.y / on_m + dy)
        if x >= 0 and y >= 0 and x < max_x and y < max_y:
            self.draw_name(dx, dy)
            r = int(self.r / on_m)
            pygame.draw.circle(screen, self.color, (x, y), r, 0)

    def run(self):
        cx, cy = self.get_center_xy()
        self.x = math.sin(self.sita) * self.center_r + cx
        self.y = math.cos(self.sita) * self.center_r + cy
        self.set_sita(self.get_dsita())
        super(RunPlanet, self).run()

    def get_w(self):  # 获取角速度
        if self.v_type == 1:
            return self.v / self.center_r
        else:
            return self.v

    def get_dsita(self):
        return self.get_w() * on_time

    def set_sita(self, new_sita):
        self.sita += new_sita
        if self.sita >= 2 * math.pi:
            self.sita = 0


class WorldControl:
    def __init__(self, dx=0, dy=0):
        self.plant = {
            "Sun": None,
            "Earth": ("Sun", 5.965 * (10 ** 24), 3185696.5, (0, 255, 255), UA),
            "Mercury": ("Sun", 3.3 * (10 ** 23), 244 * 10 ** 4, (0, 255, 255), 0.387 * UA),
            "Moon": ("Earth", 7.349 * (10 ** 22), 1738140, (0, 255, 0), 3844 * 10 ** 5),
        }
        self.plant_list = []
        for name in self.plant:
            if name == "Sun":
                sun = Sun()
                sun.set_m(2 * (10 ** 30))
                sun.set_r(696300000)
                self.plant_list.append(sun)
                self.plant[name] = sun
            else:
                tmp = RunPlanet()
                tmp.setting(self.plant[self.plant[name][0]], *(self.plant[name][1:]))
                self.plant_list.append(tmp)
                self.plant[name] = tmp

        self.is_move = False

        self.dx, self.dy = dx, dy
        self.mx, self.my = dx * 2, dx * 2
        self.dbx, self.dby = dx, dy

        self.pos = None  # 上一次pos
        self.dm = UA / 3500
        self.base_dm = UA / 3500

        self.center = 0  # 跟踪对象

    def draw(self) -> None:
        while True:
            screen.fill((0, 0, 0))
            x, y = self.plant_list[self.center].get_xy()
            for p in self.plant_list:
                p.draw(self.dx - x / on_m, self.dy - y / on_m, self.mx, self.my)
            display.update()
            self.event(pygame.event.get())
            time.sleep(world_time)

    def event(self, event_list: list):
        for event in event_list:
            if event.type == pygame.QUIT:
                exit()

            # 鼠标按下，让状态变成可以移动
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.is_move = True
                self.pos = event.pos

            # 鼠标弹起，让状态变成不可以移动
            elif event.type == pygame.MOUSEBUTTONUP:
                global on_m
                if event.button == 4:
                    self.is_move = False
                    while self.dm >= 1:
                        on_m -= self.dm
                        if on_m <= 0:
                            on_m += self.dm
                            self.dm /= 2
                        else:
                            break
                elif event.button == 5:
                    self.is_move = False
                    on_m += self.dm
                    if self.dm < self.base_dm:
                        self.dm *= 2
                else:
                    self.is_move = False
                    self.pos = None

            # 鼠标移动事件
            elif event.type == pygame.MOUSEMOTION:
                if self.is_move:
                    screen.fill((255,255,255))
                    x, y = event.pos
                    if self.pos:
                        self.dx += x - self.pos[0]
                        self.dy += y - self.pos[1]
                    self.pos = event.pos

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:
                    self.dx = self.dbx
                    self.dy = self.dby
                elif event.key == pygame.K_DOWN:
                    if self.center == 0:
                        self.center = len(self.plant_list) - 1
                    else:
                        self.center -= 1
                elif event.key == pygame.K_UP:
                    if self.center == len(self.plant_list) - 1:
                        self.center = 0
                    else:
                        self.center += 1


if __name__ == "__main__":
    center = (1200, 400)
    screen = display.set_mode((center[0] * 2, center[1] * 2), 0, 32)
    display.set_caption("物理: 天体运动")

    world = WorldControl(*center)
    world.draw()
