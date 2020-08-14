import requests
import json
from datetime import datetime as dt
from datetime import timedelta

from project.data.preprocessor import Preprocessor

date_format = '%Y-%m-%dT%H:%M:%SZ'

# For accessing the MET api
sitename = 'bergenvann-pumpedata.herokuapp.com scott.gullaksen@gmail.com'

# For accessing the Frost api
client_id = '96e12234-e9da-479b-9c42-0264c6fd51d4'
client_secret = 'd26bbc27-2378-439a-8123-4bc3e75f8478'

# urls
met_url = 'https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=60.39&lon=5.32'
frost_url = 'https://frost.met.no/observations/v0.jsonld'

location_id = {
    'florida_sentrum':  'SN50540',
    'florida_uib': 'SN50539'
}

def to_datetime(*strings):
    return tuple([
        dt.strptime(s, date_format)
        for s in strings
    ])
    
def get_dates_between(first, last):
    for x in range((last - first).seconds // 3600):
        yield first + timedelta(hours= x)
        
def check_response(r):
    if r.status_code != 200:
        raise IOError(f'Unsuccesful api request. Status: {r.status_code}, {r.reason}')

def get_weather_forecast():
    # Retrive response from endpoint
    r = requests.get(
        url= met_url,
        headers= { 'User-Agent': sitename }
    )
    
    check_response(r)
    
    expiration = r.headers['Expires']
    last_modified = r.headers['Last-Modified']
    data = json.loads(r.content)

    # Extract data
    timeseries = data['properties']['timeseries']
    
    # Further extract relevant data from each timeseries object
    last = timeseries[0]
    for dp in timeseries[1:]:

        # Need datapoints for all hours - might be gap in timeseries
        # If so, use last dp from timeseries
        dates_between = get_dates_between(*to_datetime(last['time'], dp['time']))
        dates_between = list(dates_between)
        for d in dates_between:
            yield {
                'date': d,
                'temp (C)': last['data']['instant']['details']['air_temperature'],
                'precipitation (mm)': last['data'].get(
                    'last_1_hours',
                    last['data'].get(
                        'last_6_hours',
                        {'details': {'precipitation': 0}}
                    )
                )['details']['precipitation'] / len(dates_between)
            }
            
        last = dp
        
def get_historical_weather(location, _from: dt= None, _to: dt= None):
    
    r = requests.get(
        url= frost_url,
        params= {
            'sources': location_id[location],
            'elements': 'air_temperature,sum(precipitation_amount PT1H)',
            'referencetime': '2020-04-01/2020-04-03',
        },
        auth= (client_id, '')
    )
    
    check_response(r)
    
    data = r.json()['data']
    
    return data

class api_reader(object):
    """
    Class that lets the preprocessor class treat this as a reading object.
    This way, when api calls are made, they can be easily pickled and saved in
    the existing datastructue.
    """
    
    def read(self, reader, cleaner, location):
        """
        Method required by preprocessor.
        
        Args:
            location, cleaner: not used.
            reader: specify an api callback to use.
        """
        return reader()
        
def update_weather_stations(from_date, to_date):    
    """
    Updates the pickled datastructures with data between
    the specified dates fetched from 'https://frost.met.no/observations'
    """
    
    def get_florida_uib():
        return get_historical_weather('florida_uib', from_date, to_date)
    
    def get_florida_sentrum():
        return get_historical_weather('florida_sentrum', from_date, to_date)
    
    processors = {
        'florida_sentrum': {
            'reader': get_florida_sentrum,
            'cleaner': None
        },
        'florida_uib': {
            'reader': get_florida_uib,
            'cleaner': None
        }
    }
    
    reader = api_reader()
    pp = Preprocessor(reader=reader, processors= processors)
    
    pp.transform()
    
data = list(get_weather_forecast())

r = requests.get(
    url= 'https://frost.met.no/sources/v0.jsonld',
    params= {
        'municipality': 'BERGEN'
    },
    auth= (client_id, '')
)

data = r.json()

hist_weath = get_historical_weather()

print(len(hist_weath))