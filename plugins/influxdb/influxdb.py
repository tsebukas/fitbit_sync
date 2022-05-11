from datetime import datetime
from pathlib import Path
from sys import exit
from time import time

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import yaml
import plugins

from synge import get_logger

class InfluxDB(plugins.PlugIns):
    def __init__(self, conf):
        self.name = 'influxdb'
        self.type = 'load'
        self.cfg = conf
        self.setup = None
        self.dbclient = None

        self.log = get_logger(self.__class__.__name__)

    def _load_setup(self):
        setupfile=Path(Path(__file__).parent, 'setup.yml')
        if setupfile.is_file():
            with open(setupfile, 'r') as ymlfile:
                setup = yaml.load(ymlfile, Loader=yaml.FullLoader)
        else:
            self.log.error(f'No setup file {setupfile}')
            exit(1)
        return setup[self.name]
    
    def _setup(self):
        conf_needed = [r for r in self.setup['conf_needed']]
        conf_rows = [r for r in self.cfg.yaml[self.name]]

        if all(item in conf_rows for item in conf_needed):
            self.dbclient = InfluxDBClient(url=f'http://{self.cfg.yaml[self.name]["host"]}:{self.cfg.yaml[self.name]["port"]}', token=self.cfg.yaml[self.name]["access_token"], org=self.cfg.yaml[self.name]["org"])
        else:
            self.log.error(f'Please fill all needed fields in configuration file.')
            exit(1)

    def run(self, datapoints):
        self.setup = self._load_setup()
        self._setup()
        
        self.log.debug('Starting InfluxDB sync')
        start = time()
        with self.dbclient as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            data = "mem,host=host1 used_percent=23.43234543"
            write_api.write(self.cfg.yaml[self.name]['bucket'], self.cfg.yaml[self.name]['org'], datapoints)
        # for q in self.flow:
        #     self._fetch_data(q['category'], q['type'], day)
        end = time()
        self.log.debug(f'InfluxDB syncing was successful, took {end - start} seconds')
