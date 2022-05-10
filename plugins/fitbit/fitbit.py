from datetime import datetime
from distutils.command.config import config
from pathlib import Path
from sys import exit
from time import time

import pytz
import requests
import yaml
import plugins

from synge import get_logger

class FitBit(plugins.PlugIns):
    def __init__(self, conf):
        self.name = 'fitbit'
        self.type = 'extract'
        self.cfg = conf
        self.flow = []
        self.datapoints = []
        self.setup = None
        self.token = None

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
            for category, types in self.setup['endpoints'].items():
                for type in types:
                    self.flow.append({'category' : category, 'type' : type})
        else:
            self.log.error(f'Please fill all needed fields in configuration file.')
            exit(1)
        
        self.token = self._get_token()

    def _get_token(self):
        tokenfile = self.cfg.file.parent / f'{self.name}_refreshtoken'
        try:
            if tokenfile.is_file():
                with open(tokenfile, 'r') as tf:
                    refreshtoken = tf.read()
                response = requests.post('https://api.fitbit.com/oauth2/token',
                data={
                    'client_id': self.cfg.yaml[self.name]['client_id'],
                    'grant_type': 'refresh_token',
                    'redirect_uri': self.cfg.yaml[self.name]['redirect_uri'],
                    'refresh_token': refreshtoken
                }, auth=(self.cfg.yaml[self.name]['client_id'], self.cfg.yaml[self.name]['client_secret']))
            else:
                response = requests.post('https://api.fitbit.com/oauth2/token',
                data={
                    'client_id': self.cfg.yaml[self.name]['client_id'],
                    'grant_type': 'authorization_code',
                    'redirect_uri': self.cfg.yaml[self.name]['redirect_uri'],
                    'code': self.cfg.yaml[self.name]['initial_code']
                }, auth=(self.cfg.yaml[self.name]['client_id'], self.cfg.yaml[self.name]['client_secret']))
        
            response.raise_for_status()

        except requests.exceptions.HTTPError as err:
            self.log.error(f'HTTP request failed: {err}')
            exit(1)

        json = response.json()
        newtoken = json['access_token']
        refreshtoken = json['refresh_token']
        with open(tokenfile, 'w+') as tf:
            tf.write(refreshtoken)
        
        return newtoken
    
    def _fetch_data(self, category, type, date):
        local_timezone = pytz.timezone(self.cfg.yaml['common']['timezone'])
        language = self.cfg.yaml['common']['language']
        try:
            response = requests.get(f'https://api.fitbit.com/1/user/-/{category}/{type}/date/{date}/1d.json', 
                headers={'Authorization': 'Bearer ' + self.token, 'Accept-Language': language})
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            self.log.error(f'HTTP request for {category}/{type} failed: {err}')
        else:
            data = response.json()
            value = data[category+'-'+type][0]['value']
            self.log.debug(f'Got {category}/{type}- {value}')
            
            for day in data[category.replace('/', '-') + '-' + type]:
                self.datapoints.append({
                        "measurement": type,
                        "time": local_timezone.localize(datetime.fromisoformat(day['dateTime'])).astimezone(pytz.utc).isoformat(),

                        "fields": {
                            "value": float(day['value'])
                        }
                    })
    
    def run(self, date):
        self.setup = self._load_setup()
        self._setup()
        
        self.log.debug('Starting sync')
        start = time()
        for q in self.flow:
            self._fetch_data(q['category'], q['type'], date)
        end = time()
        self.log.debug(f'Syncing was successful, took {end - start} seconds')
