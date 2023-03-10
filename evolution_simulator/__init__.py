from .main import main
from .renderer.render_nn_diagram import render_graph
# from .serializer.serializer import main as serializer


class Main:
    def __init__(self, *args):
        main(args)


# class SerializerTest:
#     def __init__(self, *a):
#         serializer()


class IGraphTest:
    def __init__(self, *a):
        pass
        # sim = main(RandomState(42))
        # graph = render_graph(sim.entities[1].nn.connections)
        # graph.save('net.png')
