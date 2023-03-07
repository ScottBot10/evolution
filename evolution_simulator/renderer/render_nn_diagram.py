from math import isnan

import igraph

from ..entity.entity_io import sensors, actions
from ..entity.genome import NEURON, SENSOR, ACTION

DEFAULT_DATA = {'size': 35}

VERTEX_DATA = [
    {
        SENSOR: {
            'vertex': lambda num: sensors[num].short_name,
            'data': {'color': 'lightblue'}
        },
        NEURON: {
            'vertex': lambda num: f'N{num}',
            'data': {'color': 'lightgrey'}
        }
    },
    {
        ACTION: {
            'vertex': lambda num: actions[num].short_name,
            'data': {'color': 'lightpink'}
        },
        NEURON: {
            'vertex': lambda num: f'N{num}',
            'data': {'color': 'lightgrey'}
        }
    }
]
NAMES = ('source', 'target')

FR = 'fr'

LAYOUT_DATA = {
    6: ((300, 300), FR),
    12: ((400, 400), FR),
    18: ((500, 500), FR),
    24: ((520, 520), FR),
    26: ((800, 800), FR),
    50: ((1000, 1000), FR),
    130: ((1200, 1200), FR),
    150: ((4000, 4000), FR, 1.5),
    200: ((4000, 4000), 'kamada_kawai', 2),
    float('NaN'): ((8000, 8000), FR),
}


def graph_from_nn(connections, vertex_datadict=None):
    vertices = []
    edges = []
    done_vertices = []

    vertex_datadict = vertex_datadict or VERTEX_DATA

    for connection in connections:
        edge = {}
        data = ((connection.inputType, connection.inputNum), (connection.outputType, connection.outputNum))
        for i, (conn_type, num) in enumerate(data):
            vertex_data = vertex_datadict[i][conn_type]
            vertex = vertex_data['vertex'](num)
            edge[NAMES[i]] = vertex
            if vertex not in done_vertices:
                vertices.append({'name': vertex, 'label': vertex, **vertex_data['data'], **DEFAULT_DATA})
                done_vertices.append(vertex)

        edge['weight'] = connection.weight
        if connection.weight < 0:
            edge['color'] = 'lightcoral'
        elif connection.weight == 0:
            edge['color'] = 'grey'
        else:
            edge['color'] = 'green'

        width = abs(connection.weight)
        edge['width'] = 1 + 1.25 * (width / 8192.0)
        edges.append(edge)

    return igraph.Graph.DictList(vertices, edges, directed=True)


def render_graph(connections, layout_data=None, vertex_datadict=None):
    g = graph_from_nn(connections, vertex_datadict)
    length = len(g.vs)
    layout_data = layout_data or LAYOUT_DATA
    for bound in sorted(layout_data):
        if length < bound or isnan(bound):
            bbox, layout, *resize_factor = layout_data[bound]
            if resize_factor:
                resize_factor = resize_factor[0]
                for v in g.vs:
                    v['size'] *= resize_factor
            break
    return igraph.plot(g, edge_curved=True, bbox=bbox, margin=64, layout=layout)
