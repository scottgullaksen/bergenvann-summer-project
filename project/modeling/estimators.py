import numpy as np

from sklearn.base import BaseEstimator, TransformerMixin

#from keras.utils import to_categorical

from util import avg

AVG_HOUR_TIDE_VALS = [
    107.58, 104.38, 97.97, 89.74, 81.83, 76.45, 75.06, 78.16,
    84.94, 93.41, 101.33, 106.50, 107.65, 104.68, 98.46, 90.46,
    82.73, 77.20, 75.43, 78.39, 85.21, 93.78, 101.73, 106.71
]

class PumpdataVectorizer(BaseEstimator, TransformerMixin):
    
    def __init__(self, pumpstation):
        self.station = pumpstation  # To be trained on
        
        # To keep track of historic values
        self.precipitation_lvls = [0.3] * 72
        
        # To compute average temperature last x hours ago
        self.temp_lvls = [8.6]  # avg temp from all recorded values
        
        # Measured pump levels from the last 24 hours
        self.pump_lvls = [-1] * 24
        
        self.snowlvl = 0
    
    def fit(self, dataset, labels= None):
        return self
    
    def update(self, datapoint):
        
        # Update pump history
        self.pump_lvls.pop(0)
        self.pump_lvls.append(datapoint[self.station]['quantity (l/s)'])
        
        # Update precipitation history
        self.precipitation_lvls.pop(0)
        self.precipitation_lvls.append(datapoint['vaerdata']['precipitation (mm)'])
        
        # Update temperature history
        if len(self.temp_lvls) == 24: self.temp_lvls.pop(0)
        self.temp_lvls.append(datapoint['vaerdata']['temp (C)'])
        
        # Update snowlevel: Only present at certain hours
        if 'snodybde' in datapoint:
            self.snowlvl = datapoint['snodybde']['snodybde (cm)']
    
    def vectorize(self, datapoint):
        date = datapoint['date']
        
        # First part are time features
        current = [date.month, date.day, date.isoweekday(), date.hour]
        
        # Add 24 most recent precipitation lvls
        current.extend(self.precipitation_lvls[-24:])
        
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
        
        return current
    
    def transform(self, dataset):
        return np.array([self.vectorize(x) for x in dataset])
    
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
	def __init__(self, model, epochs, batch_size):
		self.model = model
		self.model.save_weights('model.h5')  # Save initial weights

		# Obtained after fitting
		self.history = None

		# For fitting process
		self.epochs = epochs
		self.batch_size = batch_size
		self.val_split = 0.

	def fit(self, X, y):
		self.model.load_weights('model.h5')  # Restore untrained model before training
		self.history = self.model.fit(
			X,
			y,
			epochs= self.epochs,
			batch_size= self.batch_size,
			validation_split= self.val_split
		)
		return self

	def predict(self, X):
		return self.model.predict(X).argmax(axis= 1)

	def score(self, X, y):
		"""
		Returns loss and accuricy on the provided data set
		"""
		return self.model.evaluate(X, y)


if __name__ == "__main__":
    from project.data.reader import PickledDataReader

    station = 'Gronneviksoren'
    vectorizer = PumpdataVectorizer(station)
    vectorized = vectorizer.transform(
        [
            x for x in PickledDataReader().get_data(how= 'stream')
            if station in x
        ]
    )

    print(vectorized[:10])