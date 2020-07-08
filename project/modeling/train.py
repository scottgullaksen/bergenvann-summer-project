if __name__ == "__main__":
    from keras.models import Sequential
    from keras.layers import Dense, BatchNormalization, ReLU, Dropout
    
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    
    from modeling.estimators import PumpdataVectorizer, kerasEstimator
    from data.reader import PickledDataReader
    from modeling.util import plot_train
    
    #-------------------Load dataset------------------------------------
    reader = PickledDataReader()
    station = 'GeorgenesVerft'
    
    dataset = [x for x in reader.get_data(how='stream') if station in x]
    labels = [x[station]['quantity (l/s)'] for x in dataset]
    
    #----------------Hyperparameters-----------------------------------
    EPHOCS = 10
    BATCH_SIZE = 128
    INPUT_SIZE = (66,) # Constant
    
    #-----------------Define Keras neural net model--------------------
    
    keras_model = Sequential([
        Dense(units= 64, input_size= INPUT_SIZE),
        ReLU(),
        Dense(units= 10),
        ReLU(),
        Dense(units= 1)  # Regression
    ])
    
    #----------------Define automated pipeline-----------------------
    model = Pipeline([
        ('vectorizer', PumpdataVectorizer(station)),
        ('standarizer'), StandardScaler()  # Subtracts mean and scales by std on each feature
        ('nn', kerasEstimator(keras_model, EPHOCS, BATCH_SIZE))
    ])
    
    