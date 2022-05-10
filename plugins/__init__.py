import traceback
from pathlib import Path
from importlib import util
from synge import get_logger

class WorkFlow():
    def __init__(self, conf):
        self.flow = []
        self.datapoints = []
        self.log = get_logger(self.__class__.__name__)
        self.cfg = conf
        self._setup()
    
    def _add(self,plugin):
        self.flow.append(plugin)

    def _setup(self):
        enabled_plugins = [p for p in self.cfg.yaml]
        for p in PlugIns.installed:
            plugin = p(self.cfg)
            if (plugin.name in enabled_plugins):
                self._add(plugin)

    def run(self, day):
        for plugin in self.flow:
            if plugin.type=='extract':
                plugin.run(day)
                self.datapoints.append(plugin.datapoints)

        for plugin in self.flow:
            if plugin.type=='load':
                plugin.run(self.datapoints)

class PlugIns:
    """Basic resource class. Concrete resources will inherit from this one
    https://gist.github.com/dorneanu/cce1cd6711969d581873a88e0257e312
    """
    installed = []

    # For every class that inherits from the current,
    # the class name will be added to plugins
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.installed.append(cls)


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