import typing as t
from pathlib import Path
from time import perf_counter

import cv2 as cv
import numpy as np
from numpy.random import default_rng

from .selection_pressure import selection_pressure_renderers
from ...serializer.serializer import Coord, SerializerBase

prng = default_rng(42)

FRAME_SIZE = 900

TOP_BAR_SIZE = 100
TOP_BAR_WIDTH = 4

STEP_TIME = 0
GEN_TIME = 0


# noinspection PyUnresolvedReferences
class Renderer:
    def __init__(self, deserializer: SerializerBase.Deserializer, show_frames=True, out_dir: Path = None,
                 frame_size=FRAME_SIZE, topbar_size=TOP_BAR_SIZE, topbar_width=TOP_BAR_WIDTH,
                 step_time=STEP_TIME, gen_time=GEN_TIME):
        assert deserializer.params.grid.x == deserializer.params.grid.y
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
        panel_size = 25
        topbar_nopanel = self.topbar_size - panel_size

        self.frame_width = self.frame_size
        self.half_frame_width = self.frame_width / 2
        self.frame_height = self.frame_size + self.topbar_size + self.topbar_width

        self.step_time = step_time
        self.gen_time = gen_time

        self.circle_radius = int(self.frame_size / self.deserializer.params.grid.x / 2)
        self.circle_diameter = 2 * self.circle_radius

        self.y_offset = self.topbar_size + self.topbar_width + self.circle_radius

        self.img_base = np.full((self.frame_height, self.frame_width, 3), 255, np.uint8)
        self.img = None
        cv.line(self.img_base, (0, self.topbar_size), (self.frame_width, self.topbar_size), (0, 0, 0),
                self.topbar_width)

        bottom_text_count = 2
        bottom_piece = self.frame_size / bottom_text_count / 2
        self.bottom_text_locations = [
            self.frame_size * ((i + 1) / bottom_text_count) - bottom_piece
            for i in range(bottom_text_count)
        ]

        self.text_sizes = {}

        (text_width, text_height), text = self.get_text_size(f'Entities: {self.deserializer.params.entityCount}')
        text_height /= 2
        self.text_upper = int((topbar_nopanel * 1 / 4) - text_height / 2) + panel_size
        self.text_lower = int((topbar_nopanel * 3 / 4) - text_height / 2) + panel_size
        cv.putText(self.img_base, text, (int(self.half_frame_width - (text_width / 2)), self.text_upper),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 1, cv.LINE_AA, False)

        self.actual_width = self.circle_diameter * self.deserializer.params.grid.x
        self.actual_height = self.circle_diameter * self.deserializer.params.grid.y
        self.half_actual_width = int(self.actual_width / 2)
        self.half_actual_height = int(self.actual_height / 2)

        self.selection_pressure_renderer = selection_pressure_renderers.get(deserializer.selection_pressure.__class__)(
            self
        )
        self.img_base = self.selection_pressure_renderer.render(self.img_base)

        self.entity_colours: t.Dict[int, tuple[int, int, int]] = {}
        self.entity_positions: t.List[Coord] = []

        self.generation = -1
        self.step = self.deserializer.params.generationSteps
        self.survivors = 0

        self.finished = False
        self.wait_time = self.gen_time
        self.gen = True

    def get_text_size(self, text, scale=1):
        text_len = len(text)
        if text_len not in self.text_sizes:
            value = self.text_sizes[text_len] = cv.getTextSize(text, cv.FONT_HERSHEY_SIMPLEX, scale, cv.LINE_AA)[0]
        else:
            value = self.text_sizes[text_len]
        return value, text

    def set_entity_colours(self):
        for i in range(self.deserializer.params.entityCount):
            self.entity_colours[i] = (int(prng.integers(256)), int(prng.integers(256)), int(prng.integers(256)))

    def draw_circle_at(self, img, grid_x, grid_y, colour):
        cv.circle(img, (
            self.circle_radius + (self.circle_diameter * grid_x), self.y_offset + (self.circle_diameter * grid_y)),
                  self.circle_radius, colour, -1)

    def draw_frame(self):
        img = self.img_base.copy()
        for i, pos in enumerate(self.entity_positions):
            self.draw_circle_at(img, pos.x, pos.y, self.entity_colours[i])

        (width, _), text = self.get_text_size(f'Generation: {self.generation + 1}')
        cv.putText(img, text, (int(self.bottom_text_locations[0] - (width / 2)), self.text_lower),
                   cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 1, cv.LINE_AA, False)
        (width, _), text = self.get_text_size(f'Survivors: {self.survivors}')
        cv.putText(img, text, (int(self.bottom_text_locations[1] - (width / 2)), self.text_lower),
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

                        stats = self.deserializer.read_stats()
                        if stats is None:
                            self.finished = True
                            print('\nFinished')
                            # return perf_counter() - self.ssss
                            continue
                        self.survivors, *_ = stats
                        self.deserializer.read_genomes()
                        self.entity_positions = self.deserializer.read_initial_pos()
                        print(f"\nGeneration: {self.generation}")

                        self.set_entity_colours()

                        self.step = 0

                    if self.step == self.deserializer.params.generationSteps:
                        self.gen = True
                        self.wait_time = self.gen_time
                        self.deserializer.skip_stats()
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
