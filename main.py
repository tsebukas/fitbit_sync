from datetime import date, timedelta
from pathlib import Path

from synge import Configuration, setup_applevel_logger

from plugins import WorkFlow

logfile=Path('config', 'fitbit.log')
conffile=Path('config', 'config.yml')
log = setup_applevel_logger(file_name=logfile)


if __name__ == '__main__':
    today = (date.today()).isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    cfg = Configuration(conffile)
    
    wf=WorkFlow(cfg)
    wf.run(today)
    
    print(wf.datapoints)
    