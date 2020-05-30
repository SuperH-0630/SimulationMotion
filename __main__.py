import abc
import pygame
import pygame.draw
import pygame.display as display
import pygame.event
import math
import time

assert not pygame.init()[-1], "初始化失败(pygame存在未初始化的模块)"
on_time: float = 1000  # 一次计算的时间间隔( = 沙盘时间 / on_run)
on_run: int = 20  # 运行 on_run 次,绘图一次
world_time: float = 0.001  # 一个on_time * on_run等于实际的时间

UA = 149597870700
on_m: float = UA / 350  # 1UA的10分之一

G = 6.67 * (10 ** -11)  # 万有引力常数


class Planet(metaclass=abc.ABCMeta):
    def __init__(self):
        self.name = ""
        self.center: Planet = None
        self.x = 0
        self.y = 0
        self.dx = 0  # 每次run的时候,增加的x
        self.dy = 0

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
    def draw(self, dx, dy, max_x, max_y, is_center=True, is_draw=True):  # dx和dy是偏移量
        pass

    def get_xy(self):  # dx和dy是偏移量
        return self.x, self.y

    def get_dxy(self):  # dx和dy是偏移量
        return self.dx, self.dy

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

    def draw(self, dx, dy, max_x, max_y, is_center=True, is_draw=True) -> None:  # dx和dy是偏移量
        if not is_draw:
            return

        dx = int(dx / on_m)
        dy = int(dy / on_m)
        if (0 <= dx < max_x and 0 <= dy < max_y) or is_center:
            self.draw_name(dx, dy)
            r = int(self.r / on_m)
            pygame.draw.circle(screen, self.color, (dx, dy), r, 0)


class RunPlanet(Planet):
    def __init__(self):
        super(RunPlanet, self).__init__()
        self.sita = 0  # 与中心天体的角度
        self.last_sita = 0
        self.v = 0  # 线速度
        self.v_type = 1  # 0-角速度，1-线速度

    def setting(self, center, m, r, color, center_r, first=True):
        self.set_center(center)
        self.set_color(color)
        self.set_r(r)
        self.set_m(m)
        self.set_center_r(center_r)
        if first:
            cx, cy = center.get_xy()
            self.y = cy
            self.x = cx + self.center_r
        self.r_to_v()

    def r_to_v(self):
        v = math.sqrt(G * self.center.m / self.center_r)
        self.set_v(v, 1)

    def set_v(self, v: float, v_type: int = 1) -> None:
        self.v = v
        self.v_type = v_type

    def draw(self, dx, dy, max_x, max_y, is_center=True, is_draw=True):  # dx和dy是偏移量
        self.run()
        if not is_draw:
            return

        if is_center:
            dx += -self.x
            dy += -self.y
        x = int((self.x + dx) / on_m)
        y = int((self.y + dy) / on_m)
        if 0 <= x < max_x and 0 <= y < max_y:
            self.draw_name(dx, dy)
            r = int(self.r / on_m)
            pygame.draw.circle(screen, self.color, (x, y), r, 0)

    def run(self):
        cx, cy = self.center.get_xy()
        # 保持与中心天体相对静止
        self.dx, self.dy = self.center.get_dxy()
        sx, sy = self.get_xy()
        sx += self.dx
        sy += self.dy

        dx, dy = sx - cx, sy - cy  # 两者距离

        # self.set_center_r(math.sqrt(dx ** 2 + dy ** 2))
        # self.r_to_v()

        if dx == 0:  # 同一竖直线上
            if dy > 0:  # plant在center下面
                vx = self.v
            else:
                vx = -self.v
            vy = 0
        elif dy == 0:  # 同一竖直线上
            if dx > 0:  # plant在center下面
                vy = -self.v
            else:
                vy = self.v
            vx = 0
        else:
            new_sita = self.get_sita(dx, dy)
            center_sita = (new_sita - self.sita) / 2  # 取得前进的一半
            if self.sita > 0 and new_sita < 0:  # 跨越了180度界限
                center_sita = math.pi - center_sita

            vx = math.cos(new_sita + center_sita) * self.v  # new_sita向前一半(保证r不会慢慢变大)
            vy = -math.sin(new_sita + center_sita) * self.v
            self.last_sita = self.sita
            self.sita = new_sita
        self.dx += vx * on_time
        self.dy += vy * on_time
        self.x += self.dx
        self.y += self.dy
        super(RunPlanet, self).run()

    @staticmethod
    def get_sita(dx, dy):
        if dx > 0 and dy > 0:  # 右下
            tan_sita = dx / dy
            sita = math.atan(tan_sita)
        elif dx > 0 and dy < 0:  # 右上
            tan_sita = -dy / dx
            sita = math.atan(tan_sita) + 0.5 * math.pi  # +90度
        elif dx < 0 and dy > 0:  # 左下
            tan_sita = -dx / dy
            sita = -math.atan(tan_sita)
        else:  # 左上
            tan_sita = -dy / -dx
            sita = -math.atan(tan_sita) - 0.5 * math.pi  # +90度
        return sita

    def set_sita(self):
        cx, cy = self.center.get_xy()
        sx, sy = self.get_xy()
        dx, dy = sx - cx, sy - cy
        sin_sita = dx / dy
        self.sita = math.asin(sin_sita)
        # self.sita += new_sita
        # if self.sita >= 2 * math.pi:
        #     self.sita = 0


class WorldControl:
    def __init__(self, dx=0, dy=0):
        self.plant = {
            "Sun": None,
            "Earth": ("Sun", 5.965 * (10 ** 24), 3185696.5, (0, 255, 255), UA),
            "Mercury": ("Sun", 3.3 * (10 ** 23), 244 * 10 ** 4, (0, 255, 255), 0.387 * UA),
            "Mars": ("Sun", 6.4219 * (10 ** 23), 3397 * 10 ** 3, (0, 255, 255), 0.62 * UA),
            "Venus": ("Sun", 4.869 * (10 ** 24), 6051.8 * 10 ** 3, (0, 255, 255), 0.72 * UA),
            "Moon": ("Earth", 7.349 * (10 ** 22), 1738140, (0, 255, 0), 3844 * 10 ** 5),
            # 质量 半径 颜色 距中心天体半径
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
                tmp.set_name(name)
                self.plant_list.append(tmp)
                self.plant[name] = tmp

        self.is_move = False

        self.dx, self.dy = dx * on_m, dy * on_m  # 化成沙盒尺寸
        self.mx, self.my = dx * 2, dx * 2
        self.dbx, self.dby = self.dx, self.dy

        self.pos = None  # 上一次pos
        self.dm = UA / 3500
        self.base_dm = UA / 3500

        self.center = 0  # 跟踪对象

    def draw(self) -> None:
        draw_count = 0
        while True:
            is_draw = bool(draw_count == 0)
            if is_draw:
                screen.fill((0, 0, 0))
            self.plant_list[self.center].draw(self.dx, self.dy, self.mx, self.my, is_center=True, is_draw=is_draw)  # 先画参考对象
            x, y = self.plant_list[self.center].get_xy()  # 获取偏移
            for p in self.plant_list[::-1]:
                if p == self.plant_list[self.center]:  # 不绘制参考对象(已经绘制过了)
                    continue
                p.draw(self.dx - x, self.dy - y, self.mx, self.my, is_center=False, is_draw=is_draw)
            if is_draw:
                display.update()
                self.event(pygame.event.get())
            time.sleep(world_time)
            if is_draw:
                draw_count = on_run
            else:
                draw_count -= 1

    def new_on_m(self, old, new):
        dx = self.dx / old
        dy = self.dy / old
        dbx = self.dbx / old
        dby = self.dby / old

        self.dx = dx * new
        self.dy = dy * new
        self.dbx = dbx * new
        self.dby = dby * new

    def event(self, event_list: list):
        global on_m
        for event in event_list:
            if event.type == pygame.QUIT:
                exit(0)

            # 鼠标按下，让状态变成可以移动
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.is_move = True
                self.pos = event.pos

            # 鼠标弹起，让状态变成不可以移动
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 4:
                    self.is_move = False
                    old = on_m
                    while self.dm >= 1:
                        on_m -= self.dm
                        if on_m <= 0:
                            on_m += self.dm
                            self.dm /= 2
                        else:
                            break
                    # 调整(dx, dbx等均是沙盒距离)
                    self.new_on_m(old, on_m)
                elif event.button == 5:
                    self.is_move = False
                    old = on_m
                    on_m += self.dm
                    if self.dm < self.base_dm:
                        self.dm *= 2
                    # 调整(dx, dbx等均是沙盒距离)
                    self.new_on_m(old, on_m)
                else:
                    self.is_move = False
                    self.pos = None

            # 鼠标移动事件
            elif event.type == pygame.MOUSEMOTION:
                if self.is_move:
                    screen.fill((255, 255, 255))
                    x, y = event.pos
                    if self.pos:
                        self.dx += (x - self.pos[0]) * on_m
                        self.dy += (y - self.pos[1]) * on_m
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
