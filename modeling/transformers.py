from sklearn.base import BaseEstimator, TransformerMixin

class PumpdataVectorizer(BaseEstimator, TransformerMixin):
    
    def __init__(self):
        pass
    
    def fit(self, dataset, y= None):
        return self
    
    def transform(self, dataset):
        pass