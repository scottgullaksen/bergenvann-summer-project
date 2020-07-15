from _datetime import timedelta

from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

#from keras.utils import to_categorical

from project.modeling.util import avg
from project.data.reader import PickledDataReader as reader
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
        self.precipitation_lvls = [0] * 72
        
        # To compute average temperature last x hours ago
        self.temp_lvls = [0] * 24
        
        # Measured pump levels from the last 24 hours
        self.pump_lvls = [0] * 24
        
        self.snowlvl = 0
        
        self.tide_lvls = [0] * 24
        
        self.last_date = None  # To check if date are ordered correctly
        
        # Used when values are missing
        self.averages = [{} for i in range(12)]
        
        #self.reader = reader()
        
    def __get_averages(self, month: int):

        month_data = self.averages[month - 1]
        
        if month_data: return month_data
        
        # Convert to string (required by quiery)
        month = f'0{month}' if month < 10 else str(month)
        
        print('computing data for month ' + month)
        
        result = reader().get_data(months= [month])
        
        # Define from what stations and their measurments to include in df
        stations = {
            self.station: ['quantity (l/s)'],
            'florida_sentrum': ['precipitation (mm)', 'temp (C)'],
            'florida_uib': ['precipitation (mm)'],
            'snodybde': ['snodybde (cm)']
        }
        
        df = merge_stations(result, stations)
        
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
        
    def __hours_since_last_date(self, date):
        """
        Returns: number of hours between date and last_date
        
        raises: Exception if order of datapoints not correct
        """
        if self.last_date > date:
            raise Exception('datapoints are not fed in correct order')
        diff = date - self.last_date
        diff_hours = diff.days * 24 + diff.seconds // 3600
        if diff_hours > 1.5:
            print(f'difference between last date {self.last_date} and current {date} is {diff_hours}')
        return int(diff_hours)
    
    def __update(self, datapoint):
        """Update state/history of transformer to include new datapoint"""
        
        date = datapoint['date']
        
        # UPDATE PUMP HISTORY
        # These values should always be present
        self.pump_lvls.append(datapoint[self.station]['quantity (l/s)'])
        self.pump_lvls.pop(0)
        
        # UPDATE PRECIPITATION AND TEMP HISTORY
        # Precipitation data might not always be present
        new_val = []
        if 'florida_sentrum' in datapoint:
            new_val.append(
                datapoint['florida_sentrum']['precipitation (mm)']
            )
            self.temp_lvls.append(datapoint['florida_sentrum']['temp (C)'])
        else:
            # Use avg temp from relevant hour and month istead
            avg_vals = self.__get_averages(date.month)
            avg_temp_val = avg_vals['temperatures'][date.hour]
            self.temp_lvls.append(avg_temp_val)
    
        if 'florida_uib' in datapoint:
            new_val.append(
                datapoint['florida_uib']['precipitation (mm)']
            )
        # Set precipitation as average of weather station data
        # availeable. If not, use month average instead
        self.precipitation_lvls.append(
            np.nanmean(np.array(new_val))
            if not all(map(np.isnan, new_val))
            else self.__get_averages(datapoint['date'].month)['precipitation']
        )
        self.precipitation_lvls.pop(0)
        self.temp_lvls.pop(0)

        # UPDATE SNOWLEVEL
        # Only present at certain hours
        if 'snodybde' in datapoint:
            self.snowlvl = datapoint['snodybde']['snodybde (cm)']
            
        # UPDATE TIDE LEVEL DATA
        self.tide_lvls.append(
            datapoint['tidevannsdata']['level (cm)']
            if 'tidevannsdata' in datapoint
            else AVG_HOUR_TIDE_VALS[date.hour]  # Use avg values if data missing
        )
        self.tide_lvls.pop(0)
        
        # UPDATE DATE
        self.last_date = date
            
    def __impute_missing_dates(self, date):
        """
        Checks the date to see if the intervall from the last date
        is more than one hour. Corrects state of transformer with
        average values based on month.
        """
        
        missing_dates = [  # create sequence of dates to impute
            (date - timedelta(hours= i))
            for i in range(1, min(self.__hours_since_last_date(date), 73))
        ]
        
        if not missing_dates: return
        
        recent_data = {  # create a dict for rapid indexing
            x['date']: x  for x in reader().get_data(
                date - timedelta(days= 4),
                date,
                how= 'stream'
            )
        }
        
        for prev_date in missing_dates[::-1]:
            month_data = self.__get_averages(prev_date.month)
            datapoint = recent_data.get(prev_date, {})

            if not self.station in datapoint:
                datapoint[self.station] = {
                    'quantity (l/s)': month_data['pump_values'][prev_date.hour]
                }
        
            self.__update(datapoint)
        
        print(f'imputing for values between dates: {missing_dates[-1]} and {missing_dates[0]}')
    
    def __vectorize(self, datapoint):
        
        date = datapoint['date']
        
        self.__impute_missing_dates(date)
        
        # First part are time features
        current = [date.month, date.day, date.isoweekday(), date.hour]
        
        # Add 24 most recent precipitation lvls
        
        """current.extend(self.precipitation_lvls[48:])
        
        current.extend(  # Extend with 6 avg values from window 24-48 hours
            avg(self.precipitation_lvls[i: i + 4])
            for i in range(24, 48, 4)
        )
        
        current.extend(  # Extend with 4 avg values from window 0-24 hours
            avg(self.precipitation_lvls[i: i + 6])
            for i in range(0, 24, 6) 
        )"""
        
        # Add temperature features
        
        # current.append(avg(self.temp_lvls[-min(4, len(self.temp_lvls)):]))
        #current.append(avg(self.temp_lvls))
    
        current.append(self.snowlvl)
        
        #current.extend(self.pump_lvls)
        
        # Want to include vals from current datapoint in vector?
        # extend current AFTER update
        self.__update(datapoint)
        
        current.extend(self.temp_lvls)
        
        current.extend(self.precipitation_lvls)
        
        current.extend(self.tide_lvls)
        
        return current
    
    def fit(self, dataset, labels= None):
        return self
    
    def transform(self, dataset):
        # So the first vectors are initialized correctly:
        self.last_date = dataset[0]['date'] - timedelta(days= 4)
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
    vectorizer = PumpdataVectorizer(station)
    vectorized = vectorizer.transform(
        sorted([
            x for x in PickledDataReader().get_data(dt(2010, 4, 1),
                                                    dt(2011, 3, 13),
                                                    how= 'stream')
            if station in x
        ] + [
            x for x in PickledDataReader().get_data(dt(2011, 4, 6),
                                                    how= 'stream')
            if station in x
        ], key= lambda x: x['date'])
    )

    print(vectorized[:10])