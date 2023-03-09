import importlib
import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        module_name, class_name = sys.argv[1].rsplit('.', 1)
        try:
            module = importlib.import_module(module_name)
            clazz = getattr(module, class_name, None)
            if clazz is not None:
                clazz(*sys.argv[2:])
                # input()
        except ModuleNotFoundError:
            raise ModuleNotFoundError(f"No module named '{module_name}'")
