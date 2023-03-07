# TODO: Think of a better name for this


class VectorMeta(type):
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        if cls.enabled and cls.vector_group is not None:
            cls.vector_group.add(cls)
        return cls


class VectorGroup:
    def __init__(self, *vectors: 'Vector'):
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

    def add(self, cls):
        id = cls.id
        if id is None:
            id = self.len
        self.ids[id] = cls
        self.names[cls.__qualname__] = cls

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.ids[item]
        elif isinstance(item, str):
            return self.names[item]


class Vector(metaclass=VectorMeta):
    enabled: bool = False
    vector_group: VectorGroup = None
    id: int = None  # uint7 (0 to 127)
