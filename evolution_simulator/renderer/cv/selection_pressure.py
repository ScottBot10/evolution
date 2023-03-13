import typing as t

import cv2
import numpy as np

from ... import selection_pressure

selection_pressure_renderers: t.Dict[
    t.Type[selection_pressure.SelectionPressure], t.Type['SelectionPressureRender']] = {}

RED = (0, 0, 255)
BLACK = (255, 255, 255)


class SelectionPressureRender:
    pressure: t.Type[selection_pressure.SelectionPressure]

    def __init_subclass__(cls, **kwargs):
        selection_pressure_renderers[cls.pressure] = cls

    def __init__(self, renderer):
        pass

    def render(self, img: np.ndarray) -> np.ndarray:
        return img


class AllSurvive(SelectionPressureRender):
    pressure = selection_pressure.AllSurvive


class LeftHalf(SelectionPressureRender):
    pressure = selection_pressure.LeftHalf

    def __init__(self, renderer):
        super().__init__(renderer)
        self.half_pos = renderer.half_actual_width
        self.frame_start = renderer.topbar_size + renderer.topbar_width - 1
        self.frame_stop = self.frame_start + renderer.actual_height + 1
        self.red_square = np.full((renderer.actual_height + 1, self.half_pos, 3), RED, dtype=np.uint8)

    def render(self, img: np.ndarray) -> np.ndarray:
        img[self.frame_start:self.frame_stop, :self.half_pos] = cv2.addWeighted(
            img[self.frame_start:self.frame_stop, :self.half_pos], 0.8, self.red_square, 0.2, 1.0)
        return super().render(img)


class LeftQuarter(SelectionPressureRender):
    pressure = selection_pressure.LeftQuarter

    def __init__(self, renderer):
        super().__init__(renderer)
        self.quarter_pos = int(renderer.actual_width / 4)
        self.frame_start = renderer.topbar_size + renderer.topbar_width
        self.frame_end = self.frame_start + renderer.actual_height
        self.red_square = np.full((renderer.actual_height, self.quarter_pos, 3), RED, dtype=np.uint8)

    def render(self, img: np.ndarray) -> np.ndarray:
        img[self.frame_start:self.frame_end, :self.quarter_pos] = cv2.addWeighted(
            img[self.frame_start:self.frame_end, :self.quarter_pos], 0.8, self.red_square, 0.2, 1.0)
        return super().render(img)


class RightHalf(SelectionPressureRender):
    pressure = selection_pressure.RightHalf

    def __init__(self, renderer):
        super().__init__(renderer)
        self.half_pos = renderer.half_actual_width
        self.half_stop = renderer.actual_width

        self.frame_start = renderer.topbar_size + renderer.topbar_width - 1
        self.frame_stop = self.frame_start + renderer.actual_height + 1
        self.red_square = np.full((renderer.actual_height + 1, self.half_pos, 3), RED, dtype=np.uint8)

    def render(self, img: np.ndarray) -> np.ndarray:
        img[self.frame_start:self.frame_stop, self.half_pos:self.half_stop] = cv2.addWeighted(
            img[self.frame_start:self.frame_stop, self.half_pos:self.half_stop], 0.8, self.red_square, 0.2, 1.0)
        return super().render(img)


class RightQuarter(SelectionPressureRender):
    pressure = selection_pressure.RightQuarter

    def __init__(self, renderer):
        super().__init__(renderer)
        self.quarter_pos = int(renderer.actual_width * 3 / 4)
        self.quarter_end = renderer.actual_width

        self.frame_start = renderer.topbar_size + renderer.topbar_width
        self.frame_end = self.frame_start + renderer.actual_height

        self.red_square = np.full((renderer.actual_height, int(renderer.actual_width / 4), 3), RED, dtype=np.uint8)
        pass

    def render(self, img: np.ndarray) -> np.ndarray:
        img[self.frame_start:self.frame_end, self.quarter_pos:self.quarter_end] = cv2.addWeighted(
            img[self.frame_start:self.frame_end, self.quarter_pos:self.quarter_end], 0.8, self.red_square, 0.2, 1.0)
        return super().render(img)


class TopHalf(SelectionPressureRender):
    pressure = selection_pressure.TopHalf

    def __init__(self, renderer):
        super().__init__(renderer)
        self.frame_start = renderer.topbar_size + renderer.topbar_width - 1
        self.half_pos = self.frame_start + renderer.half_actual_height

        self.end_pos = renderer.actual_width + 1

        self.red_square = np.full((renderer.half_actual_height, self.end_pos, 3), RED, dtype=np.uint8)

    def render(self, img: np.ndarray) -> np.ndarray:
        img[self.frame_start:self.half_pos, :self.end_pos] = cv2.addWeighted(
            img[self.frame_start:self.half_pos, :self.end_pos], 0.8, self.red_square, 0.2, 1.0)
        return super().render(img)


class BottomHalf(SelectionPressureRender):
    pressure = selection_pressure.BottomHalf

    def __init__(self, renderer):
        super().__init__(renderer)
        half_height = renderer.half_actual_height
        self.half_pos = renderer.topbar_size + renderer.topbar_width + half_height
        self.end_pos = renderer.topbar_size + renderer.topbar_width + renderer.actual_height
        self.end_x = renderer.actual_width

        self.red_square = np.full((half_height, self.end_x, 3), RED, dtype=np.uint8)
        pass

    def render(self, img: np.ndarray) -> np.ndarray:
        img[self.half_pos:self.end_pos, :self.end_x] = cv2.addWeighted(img[self.half_pos:self.end_pos, :self.end_x],
                                                                       0.8, self.red_square, 0.2, 1.0)
        return super().render(img)


class Circle(SelectionPressureRender):
    pressure = selection_pressure.Circle

    def __init__(self, renderer):
        super().__init__(renderer)
        half = renderer.half_actual_width
        radius = renderer.deserializer.selection_pressure.radius * renderer.circle_diameter
        diameter = 2 * radius

        top_start = renderer.topbar_size + renderer.topbar_width

        self.start_x = half - radius
        self.end_x = half + radius

        self.start_y = self.start_x + top_start
        self.end_y = self.end_x + top_start

        self.circle = np.full((diameter, diameter, 3), 255, dtype=np.uint8)
        cv2.circle(self.circle, (radius, radius), radius, RED, -1)

    def render(self, img: np.ndarray) -> np.ndarray:
        img[self.start_y:self.end_y, self.start_x:self.end_x] = cv2.addWeighted(
            img[self.start_y:self.end_y, self.start_x:self.end_x], 0.8, self.circle, 0.2, 1.0)
        return super().render(img)
