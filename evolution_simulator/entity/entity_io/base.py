from ...vectors import VectorGroup, Vector


class Group:
    # TODO: make a better group calling system
    def execute(self, io, *a):
        io.execute_group(*a, self)

    def execute_all(self, *a):
        pass


class EntityVector(Vector):
    group: Group = None

    name: str = None
    short_name: str = None

    @classmethod
    def execute(cls, *a, **kw):
        pass
