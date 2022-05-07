from datetime import date, datetime, timedelta
from pathlib import Path
from sys import exit
from time import time

import pytz
import requests
import yaml

import logger

logfile=Path('config', 'fitbit.log')
log = logger.setup_applevel_logger(file_name=logfile)
# ajutine
LOCAL_TIMEZONE = pytz.timezone('Asia/Calcutta')

class FitBit():
    def __init__(self):
        self.log = logger.get_logger(self.__class__.__name__)
        self.cfg = self._load_conf()
        self.token = self._get_token()
        self.datapoints = []
        self.flow = []

    def _load_conf(self):
        conffile=Path('config', 'config.yml')
        if conffile.is_file():
            with open(conffile, 'r') as ymlfile:
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
                    'access_token' : ''
                    }
            }
            with open(conffile, 'w+') as ymlfile:
                yaml.dump(cfg, ymlfile)
            self.log.error(f'Please fill all fields in {conffile.name}')
            exit(1)
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
            exit(1)

        json = response.json()
        newtoken = json['access_token']
        refreshtoken = json['refresh_token']
        with open(tokenfile, 'w+') as tf:
            tf.write(refreshtoken)
        
        return newtoken
    
    def _fetch_data(self, category, type, date):
        try:
            response = requests.get('https://api.fitbit.com/1/user/-/' + category + '/' + type + '/date/'+date+'/1d.json', 
                headers={'Authorization': 'Bearer ' + self.token, 'Accept-Language': self.cfg['fitbit']['language']})
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            self.log.error(f'HTTP request for {category}/{type} failed: {err}')
        else:
            data = response.json()
            self.log.debug(f'Got {category}/{type}')
            
            for day in data[category.replace('/', '-') + '-' + type]:
                self.datapoints.append({
                        "measurement": type,
                        "time": LOCAL_TIMEZONE.localize(datetime.fromisoformat(day['dateTime'])).astimezone(pytz.utc).isoformat(),
                        "fields": {
                            "value": float(day['value'])
                        }
                    })
    
    def add(self, category, type, date):
        self.flow.append({'category' : category, 'type' : type, 'date' : date})

    def sync(self):
        self.log.debug('Starting sync')
        start = time()
        for q in self.flow:
            self._fetch_data(q['category'], q['type'], q['date'])
        end = time()
        self.log.debug(f'Syncing was successful, took {end - start} seconds')

if __name__ == '__main__':
    #juhend api registreerimiseks jne
    today = (date.today()).isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    fb=FitBit()
    activities = ['steps', 'distance', 'floors', 'elevation', 'minutesSedentary', 'minutesLightlyActive', 'minutesFairlyActive', 'minutesVeryActive', 'calories', 'activityCalories']
    for a in activities:
        fb.add('activities', a, yesterday)
    body = ['weight', 'fat', 'bmi']
    for b in body:
        fb.add('activities', b, yesterday)
    fb.sync()
    print(fb.datapoints)

