if __name__ == "__main__":
    from datetime import datetime
    
    from keras.models import Sequential
    from keras.layers import Dense, BatchNormalization, ReLU, Dropout
    from keras.optimizers import Adam
    from keras.losses import MeanSquaredError
    from keras.metrics import MeanAbsoluteError
    
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    
    from project.modeling.estimators import PumpdataVectorizer, kerasEstimator
    from project.data.reader import PickledDataReader
    from util import plot_train, plot_test_pred
    
    #-------------------Load dataset------------------------------------
    reader = PickledDataReader()
    station = 'Gronneviksoren'
    from_date = datetime(2011, 1, 1)  # Weather data available from then
    
    dataset = [
        x for x in reader.get_data(from_date,
                                   how='stream') if station in x
    ]
    labels = [x[station]['quantity (l/s)'] for x in dataset]
    
    #----------------Hyperparameters-----------------------------------
    EPHOCS = 10
    BATCH_SIZE = 512
    LR = 5e-4
    INPUT_SIZE = (66,) # Constant
    
    #-----------------Define Keras neural net model--------------------
    
    keras_model = Sequential([
        Dense(units= 64, input_shape= INPUT_SIZE),
        ReLU(),
        Dense(units= 1)
    ])
    
    keras_model.compile(
        optimizer=Adam(learning_rate= LR),
        loss= MeanSquaredError(),
        metrics= [MeanAbsoluteError()]
    )
    
    #----------------Define automated pipeline-----------------------
    model = Pipeline([
        ('vectorizer', PumpdataVectorizer(station)),
        # Subtracts mean and scales by std on each feature
        ('standarizer', StandardScaler()),
        ('nn', kerasEstimator(keras_model,
                              EPHOCS,
                              BATCH_SIZE,
                              val_split= 0.1))
    ])
    
    model.fit(dataset, labels)
    
    plot_train(model.named_steps['nn'].history)
    
    df = plot_test_pred(dataset, station, model)
    
    df.head()