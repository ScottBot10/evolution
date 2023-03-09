import random
import typing as t
from time import perf_counter

import cv2 as cv
import numpy as np

from ..serializer.serializer import Coord

random.seed(42)

FRAME_SIZE = 900

TOP_BAR_SIZE = 100
TOP_BAR_WIDTH = 4


STEP_TIME = 0.01
GEN_TIME = 2


# noinspection PyUnresolvedReferences
class Renderer:
    def __init__(self, deserializer, frame_size=FRAME_SIZE, topbar_size=TOP_BAR_SIZE, topbar_width=TOP_BAR_WIDTH,
                 step_time=STEP_TIME, gen_time=GEN_TIME):
        assert deserializer.grid.x == deserializer.grid.y
        self.deserializer = deserializer

        self.frame_size = frame_size
        self.topbar_size = topbar_size
        self.topbar_width = topbar_width

        self.frame_width = self.frame_size
        self.frame_height = self.frame_size + self.topbar_size + self.topbar_width

        self.step_time = step_time
        self.gen_time = gen_time

        self.circle_radius = int(self.frame_size / self.deserializer.grid.x / 2)
        self.circle_diameter = 2 * self.circle_radius

        self.y_offset = self.topbar_size + self.topbar_width + self.circle_radius

        self.img_base = np.full((self.frame_height, self.frame_width, 3), 255, np.uint8)
        cv.line(self.img_base, (0, self.topbar_size), (self.frame_width, self.topbar_size), (0, 0, 0),
                self.topbar_width)

        self.entity_colours: t.Dict[int, tuple[int]] = {}
        self.entity_positions: t.List[Coord] = []

        self.generation = -1
        self.step = self.deserializer.params.generationSteps

    def set_entity_colours(self):
        for i in range(self.deserializer.params.entityCount):
            self.entity_colours[i] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def draw_circle_at(self, img, grid_x, grid_y, colour):
        cv.circle(img, (self.circle_radius + (self.circle_diameter * grid_x),
                        self.y_offset + (self.circle_diameter * grid_y)),
                  self.circle_radius,
                  colour, -1)

    def draw_frame(self):
        img = self.img_base.copy()
        for i, pos in enumerate(self.entity_positions):
            self.draw_circle_at(img, pos.x, pos.y, self.entity_colours[i])
        return img

    def run(self):
        img = None
        finished = False

        wait_time = self.gen_time
        gen = True

        start = perf_counter() - wait_time
        while True:
            if not finished:
                now = perf_counter()
                if now - start >= wait_time:
                    if gen:
                        gen = False
                        wait_time = self.step_time

                        self.generation += 1
                        if self.generation:
                            self.deserializer.read_stats()

                        self.deserializer.read_genomes()
                        pos = self.deserializer.read_initial_pos()
                        if pos is None:
                            finished = True
                            print('\nFinished')
                            continue
                        print(f"\nGeneration: {self.generation}")
                        self.entity_positions = pos

                        self.set_entity_colours()

                        self.step = 0

                    if self.step == self.deserializer.params.generationSteps:
                        gen = True
                        wait_time = self.gen_time
                    else:
                        self.step += 1
                        print(f'\tStep: {self.step}', end='\r')
                        actions = self.deserializer.read_step()
                        for i, action in enumerate(actions):
                            if action:
                                self.entity_positions[i] += action

                    img = self.draw_frame()
                    start = perf_counter()
            cv.imshow('frame', img)

            if cv.waitKey(1) == ord('q'):
                break
