from numpy.random import RandomState

from .main import main
from .renderer import render
from .renderer.render_nn_diagram import render_graph
from .serializer import main as serializer


class Main:
    def __init__(self):
        main(RandomState(42))


class SerializerTest:
    def __init__(self):
        serializer()


class IGraphTest:
    def __init__(self):
        sim = main(RandomState(42))
        graph = render_graph(sim.entities[1].nn.connections)
        graph.save('net.png')


class Render:
    def __init__(self):
        with open('test.save', 'rb') as f:
            render(f)
