import traceback
from pathlib import Path
from importlib import util


class PlugIns:
    """Basic resource class. Concrete resources will inherit from this one
    https://gist.github.com/dorneanu/cce1cd6711969d581873a88e0257e312
    """
    plugins = []

    # For every class that inherits from the current,
    # the class name will be added to plugins
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.plugins.append(cls)


# Small utility to automatically load modules
def load_module(fname):
    spec = util.spec_from_file_location(fname.name, fname)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


path=Path(__file__).parent
for fname in sorted(path.rglob('*.py')):
    if not fname.name.startswith('.') and not fname.name.startswith('_'):
        try:
            load_module(fname)
        except Exception:
            traceback.print_exc()