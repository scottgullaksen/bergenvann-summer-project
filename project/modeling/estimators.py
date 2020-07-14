from _datetime import timedelta

from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

#from keras.utils import to_categorical

from util import avg
from project.data import reader
from project.util import aggregate_years, aggregate_days
from project.data.util import merge_stations

AVG_HOUR_TIDE_VALS = [
    107.58, 104.38, 97.97, 89.74, 81.83, 76.45, 75.06, 78.16,
    84.94, 93.41, 101.33, 106.50, 107.65, 104.68, 98.46, 90.46,
    82.73, 77.20, 75.43, 78.39, 85.21, 93.78, 101.73, 106.71
]

class PumpdataVectorizer(BaseEstimator, TransformerMixin):    
    def __init__(self, pumpstation):
          
        self.station = pumpstation  # To be trained on
        
        # To keep track of historic values
        self.precipitation_lvls = None
        
        # To compute average temperature last x hours ago
        self.temp_lvls = None
        
        # Measured pump levels from the last 24 hours
        self.pump_lvls = None
        
        self.snowlvl = None
        
        self.last_date = None  # To check if date are ordered correctly
        
        # Used when values are missing
        self.averages = [{}] * 12 # months
        
        self.reader = reader()
        
    def __is_initalized(self):
        """Returns true if all class fields are set"""
        return all( field is not None for field in [
            self.precipitation_lvls,
            self.temp_lvls,
            self.pump_lvls,
            self.snowlvl,
        ])
        
    def __get_averages(self, month: int):

        month_data = self.averages[month - 1]
        
        if month_data: return month_data
        
        # Convert to string (required by quiery)
        month = f'0{month}' if month < 10 else str(month)
        
        month_data = self.reader.get_data(months= [month])
        
        print('getting data for month ' + month)
        
        # Define from what stations and their measurments to include in df
        stations = {
            self.station: ['quantity (l/s)'],
            'florida_sentrum': ['precipitation (mm)', 'temp (C)'],
            'florida_uib': ['precipitation (mm)'],
            'snodybde': ['snodybde (cm)']
        }
        
        df = merge_stations(month_data, stations)
        
        # Use mean from relevant month
        # x/y prefixes are automatically added on merge when column name is the same
        # .values -> np array
        month_data['precipitation'] = np.nanmean(
            df[['precipitation (mm)_x', 'precipitation (mm)_y']].values
        )
        
        # Merge df on days, then on years
        # resulting in mean of hourly values from relevenat month
        aggregated = aggregate_days(aggregate_years(df))
        
        month_data['temperatures'] = aggregated['temp (C)'].values.tolist()
        
        month_data['pump_values'] = aggregated['quantity (l/s)'].values.tolist()
        
        month_data['snowlevel'] = df['snodybde (cm)'].mean()
        
        return month_data
        
        
    def __initialize(self, date):
        """
        If no datapoints precedes date, fill fields
        (historical data) with average values calculated from dataset
        """
        month_averages = self.__get_averages(date.month)
        self.precipitation_lvls = [month_averages['precipitation']] * 72
        self.pump_lvls = month_averages['pump_values']
        self.temp_lvls = month_averages['temperatures']
        self.snowlvl = month_averages['snowlevel']
        
        print('averga values from initialisation')
        print(self.precipitation_lvls, self.pump_lvls,
              self.temp_lvls, self.snowlvl, sep= '\n')
        
        # Retrieve data available from 4 days ago up until now
        # and update start-state with those values
        recent_data = sorted([
            x for x in self.reader.get_data(date - timedelta(days= 4),
                                            date - timedelta(days= 1),
                                            how= 'stream')
            if self.station in x
        ], key= lambda x: x['date'])
        
        for data in recent_data: self.update(data)
        
    def __check_date(self, date):
        """
        Checks if date comes after last_date
        or if the gap between the two are more than 
        one hour
        """
        if self.last_date != None:
            if self.last_date > date:
                print(f"""
                      Datapoints not read in correct order.
                      Previous date: {self.last_date}
                      Current date: {date}
                      """)
            diff = date - self.last_date
            diff_hours = diff.days * 24 + diff.seconds // 3600
            if diff_hours > 1.5:
                print(f"""
                      Warning: Difference between last date
                      {self.last_date} and current
                      {date}
                      is {diff}
                      """)
        self.last_date = date
    
    def update(self, datapoint):
        """Update state/history of transformer to include new datapoint"""
        
        # Update pump history
        # These values should always be present
        self.pump_lvls.pop(0)
        self.pump_lvls.append(datapoint[self.station]['quantity (l/s)'])
        
        # Update precipitation and temp history
        # Precipitation data might not always be present
        new_val = []
        if 'florida_sentrum' in datapoint:
            new_val.append(
                datapoint['florida_sentrum']['precipitation (mm)']
            )
            self.temp_lvls.append(datapoint['florida_sentrum']['temp (C)'])
        if 'florida_uib' in datapoint:
            new_val.append(
                datapoint['florida_uib']['precipitation (mm)']
            )
            
        if datapoint['date'] == dt(2011, 1, 1, 0):
            print('newval: ', new_val)
        # Set precipitation as average of weather station data
        # availeable. If not, use month average instead
        self.precipitation_lvls.append(
            np.nanmean(np.array(new_val)) if new_val else self.__get_averages(
                datapoint['date'].month
            )['precipitation']
        )
        self.precipitation_lvls.pop(0)
        if len(self.temp_lvls) == 24: self.temp_lvls.pop(0)

        # Update snowlevel: Only present at certain hours
        if 'snodybde' in datapoint:
            self.snowlvl = datapoint['snodybde']['snodybde (cm)']
    
    def __vectorize(self, datapoint):
        
        date = datapoint['date']
        
        if not self.__is_initalized():
            print('initializing transformer from data', date)
            self.__initialize(date)
        
        # First part are time features
        current = [date.month, date.day, date.isoweekday(), date.hour]
        
        # Add 24 most recent precipitation lvls
        current.extend(self.precipitation_lvls[48:])
        
        current.extend(  # Extend with 6 avg values from window 24-48 hours
            avg(self.precipitation_lvls[i: i + 4])
            for i in range(24, 48, 4)
        )
        
        current.extend(  # Extend with 4 avg values from window 0-24 hours
            avg(self.precipitation_lvls[i: i + 6])
            for i in range(0, 24, 6) 
        )
        
        # Add temperature features
        current.append(avg(self.temp_lvls[-min(4, len(self.temp_lvls)):]))
        current.append(avg(self.temp_lvls))
        
        # Add tide and snow level data
        if 'tidevannsdata' in datapoint:
            current.append(datapoint['tidevannsdata']['level (cm)'])
        else:  # Use avg values if data missing
            current.append(AVG_HOUR_TIDE_VALS[date.hour])
    
        current.append(self.snowlvl)
        
        current.extend(self.pump_lvls)
        
        self.update(datapoint)
        
        self.__check_date(date)
        
        return current
    
    def fit(self, dataset, labels= None):
        return self
    
    def transform(self, dataset):
        return np.array([self.__vectorize(x) for x in dataset])
    
class Shuffler(BaseEstimator, TransformerMixin):
    """Shuffle the dataset and labels inplace"""
    from sklearn.utils import shuffle
    
    def fit(self, dataset, labels= None):
        # This is where the magic happens
        pass

    # No-op
    def transform(self, dataset): return dataset

class kerasEstimator(BaseEstimator):
    """
    A sci-kit estimator wrapper for precompiled keras models.
    Change val_split field to evalute on validation set during training.
    The history variable contains the datapoints during training. Can
    be used for plotting purposes.
    """
    def __init__(self, model, epochs= 1, batch_size= 64, val_split= 0.):
        self.model = model
        
 
        # Obtained after fitting
        self.history = None

        # For fitting process
        self.epochs = epochs
        self.batch_size = batch_size
        self.val_split = val_split

    def fit(self, X, y):
        self.history = self.model.fit(
            X,
            y,
            epochs= self.epochs,
            batch_size= self.batch_size,
            validation_split= self.val_split
        )
        return self

    def predict(self, X):
        return self.model.predict(X)

    def score(self, X, y):
        """
        Returns loss and accuricy on the provided data set
        """
        return self.model.evaluate(X, y)


if __name__ == "__main__":
    from project.data.reader import PickledDataReader
    from datetime import datetime as dt

    station = 'Gronneviksoren'
    from_date = dt(2011, 1, 1)  # Weather data available from then
    vectorizer = PumpdataVectorizer(station)
    vectorized = vectorizer.transform(
        sorted([
            x for x in PickledDataReader().get_data(from_date,
                                                    how= 'stream')
            if station in x
        ], key= lambda x: x['date'])
    )

    print(vectorized[:10])