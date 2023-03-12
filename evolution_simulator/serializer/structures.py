from ctypes import c_uint64, c_int8, sizeof, c_uint16, LittleEndianStructure
from struct import Struct

UINT16_STRUCT = Struct('<H')
UINT8_STRUCT = Struct('<B')


class BytesConvertable:
    def to_bytes(self):
        # noinspection PyTypeChecker
        return bytes(self)

    @classmethod
    def from_bytes(cls, bytes_data):
        # noinspection PyUnresolvedReferences
        return cls.from_buffer_copy(bytes_data)


class Combination:
    def __init_subclass__(cls, **kwargs):
        cls.__from_buffer_copy = cls.from_buffer_copy
        cls.parts_fields = {
            field: part for _, part in cls._fields_ for field, *_ in part._fields_
        }

    def __init__(self, **kw):
        part_kwargs = {
            part: {} for _, part in self._fields_
        }

        for field, value in kw.items():
            param = self.parts_fields.get(field)
            if param is not None:
                part_kwargs[param][field] = value

        self.part_instances = {}

        for name, part in self._fields_:
            part_instance = part(**part_kwargs[part])
            self.part_instances[part] = part_instance
            setattr(self, name, part_instance)

    def __getattr__(self, item):
        part = self.parts_fields.get(item)
        if part is not None:
            if not hasattr(self, 'part_instances'):
                self.part_instances = {
                    part: getattr(self, name) for name, part in self._fields_
                }
            return getattr(self.part_instances[part], item)
        raise AttributeError


class PosStruct(LittleEndianStructure, BytesConvertable):
    _pack_ = 1
    _fields_ = [
        ('x', c_uint16, 8),  # 256
        ('y', c_uint16, 8),  # 256
    ]

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self.x}, {self.y})"


class ParamsHeader1(LittleEndianStructure, BytesConvertable):
    _pack_ = 1
    _fields_ = [
        ("selectionPressure", c_uint64, 7),  # 128
        ("selectionPressureData", c_uint64, 32),  # 4 294 967 296
        ("genomeLength", c_uint64, 13),  # 8 192
        ("hiddenNeurons", c_uint64, 12),  # 4 096
    ]


class ParamsHeader2(LittleEndianStructure, BytesConvertable):
    _pack_ = 1
    _fields_ = [
        ("grid", PosStruct),
        ("entityCount", c_uint64, 16),  # 65 536
        ("generationSteps", c_uint64, 16),  # 65 536
        ("mutationRate", c_uint64, 16)  # 65 536
    ]


class ParamsHeader(Combination, BytesConvertable, LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("params1", ParamsHeader1),
        ("params2", ParamsHeader2),
    ]


ParamsHeader_size = sizeof(ParamsHeader)


class DoubleAction(LittleEndianStructure, BytesConvertable):
    _fields_ = [
        ("moveX1", c_int8, 2),
        ("moveY1", c_int8, 2),
        ("moveX2", c_int8, 2),
        ("moveY2", c_int8, 2),
    ]


if __name__ == '__main__':
    pass
