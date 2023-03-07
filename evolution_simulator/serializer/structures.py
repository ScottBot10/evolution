import ctypes
from ctypes import c_uint64, c_int8


class ParamsHeader(ctypes.LittleEndianStructure):
    _fields_ = [
        ("gridX", c_uint64, 9),  # 512
        ("gridY", c_uint64, 9),  # 512
        ("entityCount", c_uint64, 16),  # 65 536
        ("generationSteps", c_uint64, 9),  # 512
        ("genomeLength", c_uint64, 7),  # 128
        ("hiddenNeurons", c_uint64, 4),  # 16
        ("mutationRate", c_uint64, 10)  # 1 024
    ]


class ParamsHeaderContainer(ctypes.Union):
    _fields_ = [
        ("b", ParamsHeader),
        ("asdecimal", c_uint64)
    ]


class Action(ctypes.LittleEndianStructure):
    _fields_ = [
        ("moveX", c_int8, 2),
        ("moveY", c_int8, 2)
    ]

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self.moveX}, {self.moveY})"


class ActionContainer(ctypes.Union):
    _fields_ = [
        ("b", Action),
        ("asdecimal", c_int8)
    ]

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self.b.moveX}, {self.b.moveY})"
