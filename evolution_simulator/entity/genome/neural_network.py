import typing as t
from collections import defaultdict
from dataclasses import dataclass
from math import tanh

from .genome import Gene, Genome, NEURON, SENSOR, ACTION
from ..entity_io.action_vectors import actions
from ..entity_io.sensor_vectors import sensors


# from ..entity_io import sensors, actions


@dataclass
class Neuron:
    output: int
    driven: bool


@dataclass
class Node:
    remapped_number: int = 0
    outputs: int = 0
    self_inputs: int = 0
    inputs_from_sensors_or_other_neurons: int = 0


class NeuralNetwork:
    def __init__(self, connections: t.List[Gene] = None, neurons: t.List[Neuron] = None):
        self.connections = connections or []
        self.neurons = neurons or []

    def graph(self):
        from ...renderer.render_nn_diagram import render_graph
        return render_graph(self.connections)

    @classmethod
    def from_genome(cls, genome: Genome, max_hidden_neurons):
        connections = []
        for gene in genome:
            connection = gene.b
            if connection.inputType == SENSOR:
                connection.inputNum %= sensors.len
            else:
                connection.inputNum %= max_hidden_neurons

            if connection.outputType == ACTION:
                connection.outputNum %= actions.len
            else:
                connection.outputNum %= max_hidden_neurons
            connections.append(connection)

        nodes = {}
        for connection in connections:
            if connection.outputType == NEURON:
                node = nodes.get(connection.outputNum)
                if node is None:
                    node = Node()
                    nodes[connection.outputNum] = node
                    assert connection.outputNum < max_hidden_neurons
                if connection.inputType == NEURON and connection.inputNum == connection.outputNum:
                    node.self_inputs += 1
                else:
                    node.inputs_from_sensors_or_other_neurons += 1

            if connection.inputType == NEURON:
                node = nodes.get(connection.inputNum)
                if node is None:
                    node = Node(connection.inputNum)
                    nodes[connection.inputNum] = node
                    assert connection.inputNum < max_hidden_neurons
                node.outputs += 1

        done = False
        while not done:
            done = True
            for num in list(nodes.keys()):
                node = nodes[num]
                assert num < max_hidden_neurons
                if not node.outputs or node.outputs == node.self_inputs:
                    done = False

                    for connection in connections.copy():
                        if connection.outputType == NEURON and connection.outputNum == num:
                            if connection.inputType == NEURON:
                                nodes[connection.inputNum].outputs -= 1
                            connections.remove(connection)

                    nodes.pop(num)

        assert len(nodes) < max_hidden_neurons
        for i, node in enumerate(nodes.values()):
            assert node.outputs != 0
            node.remapped_number = i

        neuron_conns = []
        action_conns = []
        for connection in connections:
            if connection.outputType == NEURON:
                neuron_conns.append(connection)
                connection.outputNum = nodes[connection.outputNum].remapped_number
            elif connection.outputType == ACTION:
                action_conns.append(connection)
            if connection.inputType == NEURON:
                connection.inputNum = nodes[connection.inputNum].remapped_number

        neurons = [Neuron(0.5, node.inputs_from_sensors_or_other_neurons != 0) for node in nodes.values()]
        return cls(neuron_conns + action_conns, neurons)

    def feed_forward(self, entity, simulator):
        action_levels = defaultdict(int)
        neuron_accumulators = [0] * len(self.neurons)

        neuron_outputs_completed = False
        for connection in self.connections:
            if connection.outputType == ACTION and not neuron_outputs_completed:
                for i in range(len(self.neurons)):
                    neuron = self.neurons[i]
                    if neuron.driven:
                        neuron.output = tanh(neuron_accumulators[i])
                neuron_outputs_completed = True

            if connection.inputType == SENSOR:
                input_val = sensors[connection.inputNum].execute(entity, simulator)  # Get sensor
            else:
                input_val = self.neurons[connection.inputNum].output

            updated = input_val * connection.float_weight()
            if connection.outputType == ACTION:
                action_levels[connection.outputNum] += updated
            else:
                neuron_accumulators[connection.outputNum] += updated
        return action_levels
