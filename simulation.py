import pygame as pg
from pygame import Rect
from pyopt_tools.colors import Color
import numpy as np

SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720


class Dot(pg.sprite.Sprite):

    def __init__(self, parent, x, y, width, height, color=Color.Black, radius=5, velocity=[0, 0], randomize=False):
        pg.sprite.Sprite.__init__(self)

        self.parent = parent
        self.image = pg.Surface(
            (radius * 2, radius * 2),
            pg.SRCALPHA
        ).convert_alpha()
        self.image.fill((0, 0, 0, 0))
        pg.draw.circle(self.image, color, (radius, radius), radius)

        self.rect: Rect = self.image.get_rect()
        self.pos = np.array([x, y], dtype=np.float64)
        self.vel = np.asarray(velocity, dtype=np.float64)

        self.kill_switch_on = False
        self.recoverd = False
        self.randomize = randomize

        self.WIDTH = width
        self.HEIGHT = height

    def update(self):
        self.pos += self.vel
        x, y = self.pos

        # Periodic
        if x < 0:
            self.pos[0] = self.WIDTH
            x = self.WIDTH
        if x > self.WIDTH:
            self.pos[0] = 0
            x = 0
        if y < 0:
            self.pos[1] = self.HEIGHT
            y = self.HEIGHT
        if y > self.HEIGHT:
            self.pos[1] = 0
            y = 0

        self.rect.x = x
        self.rect.y = y

        vel_norm = np.linalg.norm(self.vel)
        if vel_norm > 3:
            self.vel /= vel_norm

        if self.randomize:
            self.vel += np.random.rand(2) * 2 - 1

        if self.kill_switch_on:
            self.cycles_to_fate -= 1

            if self.cycles_to_fate <= 0:
                self.kill_switch_on = False
                some_num = np.random.rand()
                if self.moratlity_rate > some_num:
                    self.parent.dead += 1
                    self.kill()
                else:
                    self.recoverd = True

    def respawn(self, color, radius=5):
        return Dot(
            self.parent,
            self.rect.x,
            self.rect.y,
            self.WIDTH,
            self.HEIGHT,
            color=color,
            velocity=self.vel
        )

    def killswitch(self, cycles=20, moratlity_rate=20):
        self.kill_switch_on = True
        self.cycles_to_fate = cycles
        self.moratlity_rate = moratlity_rate


class Simulation:

    def __init__(self, width=1280, height=720, n_susceptible=20, n_infected=1, cycles_to_fate=20, mortality_rate=0.2):
        self.WIDTH = width
        self.HEIGHT = height

        self.susceptible_container = pg.sprite.Group()
        self.infected_container = pg.sprite.Group()
        self.recovered_container = pg.sprite.Group()
        self.all_container = pg.sprite.Group()

        self.n_susceptible = n_susceptible
        self.n_infected = n_infected
        self.cycles_to_fate = cycles_to_fate
        self.mortality_rate = mortality_rate

    def start(self, randomize=False, kill_initial_infected=False):
        '''
        randomize: randomize the movment of each dot 

        kill_initial_infected: enable killswitch for the initial infected dots that started the virus with a mortality rate,
        makes it more realistic as there is a chance the one that started it could die before spreading
        '''
        self.N = self.n_susceptible + self.n_infected
        pg.init()

        self.text_font = pg.font.SysFont("Arial", 18, italic=True)
        self.big_font = pg.font.SysFont("Arial", 25, bold=True)

        screen = pg.display.set_mode((self.WIDTH, self.HEIGHT))
        pg.display.set_caption("Simulation")
        clock = pg.time.Clock()

        for _ in range(self.n_susceptible):
            x = np.random.randint(0, self.WIDTH + 1)
            y = np.random.randint(0, self.WIDTH + 1)
            vel = np.random.rand(2) * 2 - 1
            dot = Dot(self, x, y, self.WIDTH, self.HEIGHT,
                      Color.LightSeaGreen, velocity=vel,
                      randomize=randomize
                    )
            self.susceptible_container.add(dot)
            self.all_container.add(dot)

        for _ in range(self.n_infected):
            x = np.random.randint(0, self.WIDTH + 1)
            y = np.random.randint(0, self.HEIGHT + 1)
            vel = np.random.rand(2) * 2 - 1
            dot = Dot(self, x, y, self.WIDTH, self.HEIGHT, Color.Red, velocity=vel, randomize=randomize)
            if kill_initial_infected:
                dot.killswitch(50, .1)
            self.infected_container.add(dot)
            self.all_container.add(dot)

        self.dead = 0
        while True:

            for event in pg.event.get():
                if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                    pass
                if event.type == pg.QUIT:
                    pg.quit()
                    quit(0)

            # draw main
            self.all_container.update()
            screen.fill(Color.White)

            # new infecitons
            collision_group = pg.sprite.groupcollide(
                self.susceptible_container,
                self.infected_container,
                True,
                False
            )

            for dot in collision_group:
                new_dot = dot.respawn(Color.Red)
                new_dot.vel *= -1
                new_dot.killswitch(
                    self.cycles_to_fate,
                    self.mortality_rate,
                )
                self.infected_container.add(new_dot)
                self.all_container.add(new_dot)

            # recoveries
            recovered = []
            for dot in self.infected_container:
                if dot.recoverd:
                    new_dot = dot.respawn(Color.Purple)
                    self.recovered_container.add(new_dot)
                    self.all_container.add(new_dot)
                    recovered.append(dot)

            if len(recovered) > 0:
                self.infected_container.remove(*recovered)
                self.all_container.remove(*recovered)

            self.all_container.draw(screen)

            total_population = self.text_font.render(
                    f"Total Population: {len(self.all_container)}", True, Color.Blue)   
            susceptible_container = self.text_font.render(
                    f"Susceptible: {len(self.susceptible_container)}", True, Color.LightSeaGreen)            
            infected_text = self.text_font.render(
                f"Infected: {len(self.infected_container)}", True, Color.Red)
            recovered_text = self.text_font.render(
                f"Recovered: {len(self.recovered_container)}", True, Color.Purple)
            dead_text = self.text_font.render(
                f"Dead: {self.dead}", True, Color.DarkGrey)

            screen.blit(total_population, (10, 10))
            screen.blit(susceptible_container, (10, 30))
            screen.blit(infected_text, (10, 50))
            screen.blit(recovered_text, (10, 70))
            screen.blit(dead_text, (10, 90))

            if len(self.infected_container) == 0 or len(self.susceptible_container) == 0:
                sim_end = self.big_font.render(
                    "There are no more infected" if len(self.infected_container) == 0 else "There are no more Susceptible",
                    True,
                    Color.Red
                )
                screen.blit(sim_end, (self.WIDTH//3.5, self.HEIGHT//2.5))

            
            pg.display.update()
            clock.tick(60)


if __name__ == "__main__":
    sim = Simulation(
        width=800,
        height=500,
        n_susceptible=100,
        n_infected=1
    )
    sim.n_susceptible = 80
    sim.cycles_to_fate = 200
    sim.start(randomize=True, kill_initial_infected=False)
