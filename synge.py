import logging
import sys
from pathlib import Path

import yaml

###### logger
APP_LOGGER_NAME = 'Synge'

def setup_applevel_logger(logger_name = APP_LOGGER_NAME, 
                        is_debug=True, 
                        file_name=None):
    # https://towardsdatascience.com/the-reusable-python-logging-template-for-all-your-data-science-apps-551697c8540
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG if is_debug else logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.handlers.clear()
    logger.addHandler(sh)

    if file_name:
        fh = logging.FileHandler(file_name)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


def get_logger(module_name):
    return logging.getLogger(APP_LOGGER_NAME).getChild(module_name)

###### Configuraton
class Configuration():
    def __init__(self, configuration_file):
        self.log = get_logger(self.__class__.__name__)
        self.file = configuration_file
        self.yaml = self._load_conf()
        
    
    def _load_conf(self):
        # conffile=Path('config', 'config.yml')
        if self.file.is_file():
            with open(self.file, 'r') as ymlfile:
                cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
        else:
            cfg={
                'fitbit':{
                    'language' : 'en_US',
                    'client_id' : '',
                    'client_secret' : '',
                    'initial_code' : '',
                    'redirect_uri' :  ''
                    },
                'influxdb':{
                    'host' : '',
                    'port' : '',
                    'access_token' : '',
                    'org' : '',
                    'bucket' : ''
                    }
            }
            with open(self.file, 'w+') as ymlfile:
                yaml.dump(cfg, ymlfile)
            self.log.error(f'Please fill all fields in {self.file.name}')
            exit(1)
        return cfg
