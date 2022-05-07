import sys
from pathlib import Path

import requests
import yaml

import logger

logfile=Path('config', 'fitbit.log')
log = logger.setup_applevel_logger(file_name=logfile)

class FitBit():
    def __init__(self):
        self.log = logger.get_logger(self.__class__.__name__)
        self.log.debug('Starting sync')
        self.cfg = self._load_conf()
        self.token = self._get_token()
        datapoints=[]

    def _load_conf(self):
        conffile=Path('config', 'config.yml')
        if conffile.is_file():
            with open(conffile, 'r') as ymlfile:
                cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
        else:
            cfg={
                'fitbit':{
                    'language' : '',
                    'client_id' : '',
                    'client_secret' : '',
                    'initial_code' : '',
                    'redirect_uri' :  ''
                    },
                'influxdb':{
                    'host' : '',
                    'port' : '',
                    'access_token' : ''
                    }
            }
            with open(conffile, 'w+') as ymlfile:
                yaml.dump(cfg, ymlfile)
            self.log.error(f'Please fill all fields in {conffile.name}')
            sys.exit(1)
        return cfg
    
    def _get_token(self):
        tokenfile = Path('config', 'refreshtoken')
        try:
            if tokenfile.is_file():
                with open(tokenfile, 'r') as tf:
                    refreshtoken = tf.read()
                response = requests.post('https://api.fitbit.com/oauth2/token',
                data={
                    'client_id': self.cfg['fitbit']['client_id'],
                    'grant_type': 'refresh_token',
                    'redirect_uri': self.cfg['fitbit']['redirect_uri'],
                    'refresh_token': refreshtoken
                }, auth=(self.cfg['fitbit']['client_id'], self.cfg['fitbit']['client_secret']))
            else:
                response = requests.post('https://api.fitbit.com/oauth2/token',
                data={
                    'client_id': self.cfg['fitbit']['client_id'],
                    'grant_type': 'authorization_code',
                    'redirect_uri': self.cfg['fitbit']['redirect_uri'],
                    'code': self.cfg['fitbit']['initial_code']
                }, auth=(self.cfg['fitbit']['client_id'], self.cfg['fitbit']['client_secret']))
        
            response.raise_for_status()

        except requests.exceptions.HTTPError as err:
            self.log.error(f'HTTP request failed: {err}')
            # print(response.request.url)
            # print(response.request.body)
            # print(response.request.headers)
            sys.exit(1)

        json = response.json()
        newtoken = json['access_token']
        refreshtoken = json['refresh_token']
        with open(tokenfile, 'w+') as tf:
            tf.write(refreshtoken)
        
        return newtoken



if __name__ == '__main__':
    #juhend api registreerimiseks jne
    fb=FitBit()
    print(fb.token)
    # for section in fb.cfg:
    #     print(section)
    # print(fb.cfg['fitbit'])
    # print(fb.cfg['influxdb'])
    # print(fb.cfg['influxdb']['host'])
