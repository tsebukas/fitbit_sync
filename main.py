from datetime import date, timedelta
from pathlib import Path

import synge

from plugins import PlugIns

logfile=Path('config', 'fitbit.log')
conffile=Path('config', 'config.yml')
log = synge.setup_applevel_logger(file_name=logfile)


if __name__ == '__main__':
    today = (date.today()).isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    cfg = synge.Configuration(conffile)
    enabled_plugins = [p for p in cfg.yaml]

    for p in PlugIns.plugins:
        inst = p(cfg)
        if (inst.name in enabled_plugins) and inst.type=='extract':
            inst.run(today)
            print(inst.datapoints)

