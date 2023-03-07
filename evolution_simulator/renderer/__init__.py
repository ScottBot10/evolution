import random
from time import perf_counter

import cv2 as cv
import numpy as np

from ..serializer import get_deserializer

random.seed(42)

FRAME_SIZE = 900

TOP_BAR_SIZE = 100
TOP_BAR_WIDTH = 4

FRAME_WIDTH = FRAME_SIZE
FRAME_HEIGHT = FRAME_SIZE + TOP_BAR_SIZE + TOP_BAR_WIDTH

FPS_FRAME_BUFF = 10


class Renderer:
    def __init__(self, deserializer, frame_size=FRAME_SIZE, topbar_size=TOP_BAR_SIZE, topbar_width=TOP_BAR_WIDTH,
                 fps_print=FPS_FRAME_BUFF):
        assert deserializer.params.gridX == deserializer.params.gridY
        self.deserializer = deserializer

        self.frame_size = frame_size
        self.topbar_size = topbar_size
        self.topbar_width = topbar_width

        self.frame_width = self.frame_size
        self.frame_height = self.frame_size + self.topbar_size + self.topbar_width

        self.fps_print = fps_print

        self.circle_radius = int(self.frame_size / self.deserializer.params.gridX / 2)
        self.circle_diameter = 2 * self.circle_radius

        self.y_offset = self.topbar_size + self.topbar_width + self.circle_radius

        self.img_base = np.full((self.frame_height, self.frame_width, 3), 255, np.uint8)

        self.frame = 0
        self.start_time = perf_counter()

        self.entity_cache = {}

        for i in range(self.deserializer.params.gridX * self.deserializer.params.gridY):
            self.entity_cache[i] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def draw_circle_at(self, img, grid_x, grid_y, colour):
        cv.circle(img, (self.circle_radius + (self.circle_diameter * grid_x),
            self.y_offset + (self.circle_diameter * grid_y)),
                  self.circle_radius,
                  colour, -1)

    def run(self):
        while True:
            if self.frame % self.fps_print == 0:
                now = perf_counter()
                print(f'Frame rate: {self.fps_print / (now - self.start_time):.3f}', end='\r')
                self.start_time = now
            img = self.img_base.copy()

            cv.line(img, (0, self.topbar_size), (self.frame_width, self.topbar_size), (0, 0, 0), self.topbar_width)
            for row in range(self.deserializer.params.gridX):
                for column in range(self.deserializer.params.gridY):
                    # if x > 4095:
                    #     print()
                    self.draw_circle_at(img, column, row,
                                        self.entity_cache[(row * self.deserializer.params.gridY) + column])
            cv.imshow('frame', img)
            self.frame += 1
            if cv.waitKey(1) == ord('q'):
                break


def render(fd):
    deserializer = get_deserializer(fd)
    r = Renderer(deserializer)
    r.run()
