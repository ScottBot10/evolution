import argparse
import gzip
from pathlib import Path

from numpy.random import default_rng


def main(args):
    args = parser.parse_args(args=args)
    return args.func(args)


def evolve(args):
    from .simulator import Simulator

    prng = default_rng(seed=args.seed)

    if args.generations is not None:
        def until(sim):
            return sim.generation == args.generations
    else:
        until = None

    with gzip.open(args.filename, 'wb') as f:
        simulator = Simulator(prng, f)
        simulator.run(until=until)

    return simulator


def render(args):
    from .serializer.serializer import get_serializer
    from .renderer.cv import Renderer

    renderer_args = {}
    for argname in renderer_argnames:
        attr = getattr(args, argname)
        if attr is not None:
            renderer_args[argname] = attr

    with gzip.open(args.filename, 'rb') as f:
        deserializer = get_serializer(f).Deserializer()
        renderer = Renderer(
            deserializer,
            **renderer_args
        )
        return renderer.run()


def valid_file(path):
    if (file := Path(path)).is_file():
        return file
    else:
        raise FileNotFoundError(path)


parser = argparse.ArgumentParser(
    prog='evolution_simulator',
    description='Evolution simulator in a grid',

)

parser.add_argument('-v', '--verbose', action='count', default=0)
subparsers = parser.add_subparsers(required=True, title='subcommands')

evolve_parser = subparsers.add_parser('evolve')
evolve_parser.set_defaults(func=evolve)
evolve_parser.add_argument('-o', '--output', dest='filename', required=True, metavar='FILE', type=Path)
evolve_parser.add_argument('--seed', type=int, default=42)
evolve_parser.add_argument('-g', '--generations', type=int)

render_parser = subparsers.add_parser('render')
render_parser.set_defaults(func=render)
render_parser.add_argument('-i', '--input', dest='filename', required=True, metavar='FILE', type=valid_file)
render_parser.add_argument('-o', '--output', dest='out_dir', metavar='FILE', type=Path)
render_parser.add_argument('--hide-frames', dest='show_frames', action='store_false', default=True)
render_parser.add_argument('--frame-size', dest='frame_size', type=int)
render_parser.add_argument('--topbar-size', dest='topbar_size', type=int)
render_parser.add_argument('--topbar-width', dest='topbar_width', type=int)
render_parser.add_argument('--step-time', dest='step_time', type=float)
render_parser.add_argument('--gen-time', dest='gen_time', type=float)

renderer_argnames = ('out_dir', 'show_frames', 'frame_size', 'topbar_size', 'topbar_width', 'step_time', 'gen_time')
