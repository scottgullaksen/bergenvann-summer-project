from sklearn.base import BaseEstimator, TransformerMixin
from util import avg
import numpy as np

class PumpdataVectorizer(BaseEstimator, TransformerMixin):
    
    def __init__(self, pumpstation):
        self.station = pumpstation  # To be trained on
        
        # To keep track of historic values
        self.precipitation_lvls = [-1] * 72
        
        # To compute average temperature last x hours ago
        self.temp_lvls = [9.0]  # avg temp from all recorded values
        
        # Measured pump levels from the last 24 hours
        self.pump_lvls = [-1] * 24
    
    def fit(self, dataset, y= None):
        return self
    
    def vectorize(self, datapoint):
        date = datapoint['date']
        
        # First part are time features
        current = [date.month(), date.day(), date.isoweekday(), date.hour()]
        
        # Add 24 most recent precipitation lvls
        current.extend(self.precipitation_lvls[-24:])
        
        current.extend(  # Extend with 6 avg values from window 24-48 hours
            avg(self.precipitation_lvls[i: i + 4])
            for i in range(24, 48, 4)
        )
        
        current.extend(  # Extend with 4 avg values from window 0-24 hours
            avg(self.precipitation_lvls[i: i + 6])
            for i in range(24, step= 6) 
        )
        
        # Add temperature features
        current.append(avg(self.temp_lvls[-4:]))
        current.append(avg(self.temp_lvls))
        
        # Add tide and snow level data
        current.append(datapoint['tidevannsdata']['level (cm)'])
        current.append(datapoint['snodybde']['snodybde (cm)'])
        
        current.extend(self.pump_lvls)
        
        # Update with new values
        zipped = zip(
            [
                datapoint[self.station]['quantity (l/s)'],
                datapoint['vaerdata']['precipitation (mm)'],
                datapoint['vaerdata']['temp (C)']
            ],
            [
                self.pump_lvls, self.precipitation_lvls, self.temp_lvls
            ]
        )
        for new_val, old_vals in zipped:
            old_vals.pop(0)
            old_vals.append(new_val)
        
        return current
    
    def transform(self, dataset):
        return np.array(map(self.vectorize, dataset))