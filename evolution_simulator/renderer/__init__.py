from numpy.random import default_rng
import typing as t
from pathlib import Path
from time import perf_counter

import cv2 as cv
import numpy as np

from ..serializer.serializer import Coord, SerializerBase

prng = default_rng(42)

FRAME_SIZE = 900

TOP_BAR_SIZE = 100
TOP_BAR_WIDTH = 4

STEP_TIME = 0
GEN_TIME = 0


# noinspection PyUnresolvedReferences
class Renderer:
    def __init__(self, deserializer: SerializerBase.Deserializer, show_frames=True, out_dir: Path = None,
                 frame_size=FRAME_SIZE,topbar_size=TOP_BAR_SIZE, topbar_width=TOP_BAR_WIDTH,
                 step_time=STEP_TIME, gen_time=GEN_TIME):
        assert deserializer.grid.x == deserializer.grid.y
        self.ssss = perf_counter()
        self.deserializer = deserializer

        self.show_frames = show_frames
        self.out_dir = out_dir
        if self.out_dir is not None:
            if not self.out_dir.exists():
                self.out_dir.mkdir()
            self.save_frames = self.out_dir
        else:
            self.save_frames = None

        self.frame_size = frame_size
        self.topbar_size = topbar_size
        self.topbar_width = topbar_width

        self.frame_width = self.frame_size
        self.frame_height = self.frame_size + self.topbar_size + self.topbar_width

        self.top_panel_height = 30

        self.step_time = step_time
        self.gen_time = gen_time

        self.circle_radius = int(self.frame_size / self.deserializer.grid.x / 2)
        self.circle_diameter = 2 * self.circle_radius

        self.y_offset = self.topbar_size + self.topbar_width + self.circle_radius

        self.img_base = np.full((self.frame_height, self.frame_width, 3), 255, np.uint8)
        self.img = None
        cv.line(self.img_base, (0, self.topbar_size), (self.frame_width, self.topbar_size), (0, 0, 0),
                self.topbar_width)
        j, self.text_height = cv.getTextSize(f'Entities: {self.deserializer.params.entityCount}',
                                             cv.FONT_HERSHEY_SIMPLEX, 1, cv.LINE_AA)[0]
        cv.putText(self.img_base, f'Entities: {self.deserializer.params.entityCount}', (0, self.top_panel_height),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 1, cv.LINE_AA, False)

        self.entity_colours: t.Dict[int, tuple[int, int, int]] = {}
        self.entity_positions: t.List[Coord] = []

        self.generation = -1
        self.step = self.deserializer.params.generationSteps

        self.finished = False
        self.wait_time = self.gen_time
        self.gen = True

    def set_entity_colours(self):
        for i in range(self.deserializer.params.entityCount):
            self.entity_colours[i] = (int(prng.integers(256)), int(prng.integers(256)), int(prng.integers(256)))

    def draw_circle_at(self, img, grid_x, grid_y, colour):
        cv.circle(img, (self.circle_radius + (self.circle_diameter * grid_x),
                        self.y_offset + (self.circle_diameter * grid_y)),

                  self.circle_radius,
                  colour, -1)

    def draw_frame(self):
        img = self.img_base.copy()
        for i, pos in enumerate(self.entity_positions):
            self.draw_circle_at(img, pos.x, pos.y, self.entity_colours[i])
        cv.putText(img, f'Generation: {self.generation}', (0, self.topbar_size-self.text_height),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 1, cv.LINE_AA, False)
        return img

    def run(self):
        self.gen = True

        start = perf_counter() - self.wait_time
        while True:
            if not self.finished:
                now = perf_counter()
                if now - start >= self.wait_time:
                    if self.gen:
                        self.gen = False
                        self.wait_time = self.step_time

                        self.generation += 1
                        if self.generation:
                            self.deserializer.read_stats()

                        self.deserializer.read_genomes()
                        pos = self.deserializer.read_initial_pos()
                        if pos is None:
                            self.finished = True
                            print('\nFinished')
                            # return perf_counter() - self.ssss
                            continue
                        print(f"\nGeneration: {self.generation}")
                        self.entity_positions = pos

                        self.set_entity_colours()

                        self.step = 0

                    if self.step == self.deserializer.params.generationSteps:
                        self.gen = True
                        self.wait_time = self.gen_time
                    else:
                        self.step += 1
                        print(f'\tStep: {self.step}', end='\r')
                        actions = self.deserializer.read_step()
                        for i, action in enumerate(actions):
                            if action:
                                self.entity_positions[i] += action

                    self.img = self.draw_frame()
                    if self.save_frames:
                        cv.imwrite(str(self.out_dir / f"{self.generation}-{self.step}.jpg"), self.img)
                    start = perf_counter()
            if self.show_frames:
                cv.imshow('frame', self.img)

                if cv.waitKey(1) == ord('q'):
                    break
