# TODO: Think of a better name for this
import typing as t


class VectorGroup:
    def __init__(self, *vectors: t.Type['Vector']):
        self.ids = {}
        self.names = {}
        if vectors:
            for vector in vectors:
                self.add(vector)

    def check(self):
        return self.len == self.max + 1

    @property
    def max(self):
        return max(self.ids.keys())

    @property
    def len(self):
        return len(self.ids)

    def __len__(self):
        return self.len

    def add(self, cls: t.Type['Vector']):
        cls_id = cls.id
        if cls_id is None:
            cls_id = self.len
        self.ids[cls_id] = cls
        self.names[cls.__qualname__] = cls

    def __getitem__(self, item: int | str):
        if isinstance(item, int):
            return self.ids[item]
        elif isinstance(item, str):
            return self.names[item]


class Vector:
    enabled: bool = False
    vector_group: VectorGroup = None
    id: int = None  # uint7 (0 to 127)

    def __init_subclass__(cls):
        if cls.enabled and cls.vector_group is not None:
            cls.vector_group.add(cls)
