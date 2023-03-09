from ctypes import c_uint64, c_int8, c_uint8, c_uint16, LittleEndianStructure, Union


class PosStruct(LittleEndianStructure):
    _fields_ = [
        ('x', c_uint16, 8),  # 256
        ('y', c_uint16, 8),  # 256
    ]

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self.x}, {self.y})"


class PosStructContainer(Union):
    _fields_ = [
        ("b", PosStruct),
        ("asdecimal", c_uint16)
    ]


class ParamsHeader(LittleEndianStructure):
    _fields_ = [
        ("grid", c_uint64, 16),
        ("entityCount", c_uint64, 16),  # 65 536
        ("generationSteps", c_uint64, 9),  # 512
        ("genomeLength", c_uint64, 7),  # 128
        ("hiddenNeurons", c_uint64, 4),  # 16
        ("mutationRate", c_uint64, 12)  # 4 096
    ]


class ParamsHeaderContainer(Union):
    _fields_ = [
        ("b", ParamsHeader),
        ("asdecimal", c_uint64)
    ]


class Action(LittleEndianStructure):
    _fields_ = [
        ("moveX", c_int8, 2),
        ("moveY", c_int8, 2)
    ]

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self.moveX}, {self.moveY})"


class ActionContainer(Union):
    _fields_ = [
        ("b", Action),
        ("asdecimal", c_uint8)
    ]


class DoubleAction(LittleEndianStructure):
    _fields_ = [
        ("a1", c_uint8, 4),
        ("a2", c_uint8, 4)
    ]


class DoubleActionContainer(Union):
    _fields_ = [
        ("b", DoubleAction),
        ("asdecimal", c_uint8)
    ]

    @classmethod
    def from_actions(cls, a1: Action, a2: Action):
        return cls(DoubleAction(
            a1=ActionContainer(a1).asdecimal,
            a2=ActionContainer(a2).asdecimal
        ))

    def to_actions(self):
        return ActionContainer(asdecimal=self.b.a1).b, ActionContainer(asdecimal=self.b.a2).b
