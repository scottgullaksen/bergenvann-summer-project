import requests
import json
from datetime import datetime as dt

sitename = 'bergenvann-pumpedata.herokuapp.com scott.gullaksen@gmail.com'

def get_weather_forecast():
    endpoint_url = 'https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=60.39&lon=5.32'

    headers = {
        'User-Agent': sitename
    }

    response = requests.get(endpoint_url, headers=headers)

    if response.status_code == 200:
        expiration = response.headers['Expires']
        last_modified = response.headers['Last-Modified']
        data = json.loads(response.content)
        return data
    else:
        print(f'Unsuccesful api request. Status: {response.status_code}, {response.reason}')
    
data = get_weather_forecast()