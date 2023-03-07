from .simulator import Simulator


def main(prng):
    with open('test2.save', 'wb+') as f:
        simulator = Simulator(prng, f)
        simulator.run(until=lambda sim: sim.generation == 11)

    return simulator
