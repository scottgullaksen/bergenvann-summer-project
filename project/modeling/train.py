if __name__ == "__main__":
    from datetime import datetime
    import matplotlib.pyplot as plt
    
    from keras.models import Sequential
    from keras.layers import Dense, BatchNormalization, ReLU, Dropout
    from keras.optimizers import Adam
    from keras.losses import MeanSquaredError
    from keras.metrics import MeanAbsoluteError
    
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    
    from project.modeling.estimators import PumpdataVectorizer, kerasEstimator
    from project.data.reader import PickledDataReader
    from util import plot_train, create_pred_dataframe, save, load
    
    #-------------------Load dataset------------------------------------
    reader = PickledDataReader()
    station = 'Gronneviksoren'
    from_date = datetime(2011, 1, 1)  # Weather data available from then
    
    dataset = [
        x for x in reader.get_data(from_date,
                                   how='stream') if station in x
    ]
    labels = [x[station]['quantity (l/s)'] for x in dataset]
    
    #----------------Training parameters-----------------------------------
    EPHOCS = 200
    BATCH_SIZE = 512
    LR = 5e-4
    INPUT_SIZE = (66,) # Constant
    
    
    #------------Define keras neural net model---------------------------
    def build_fcnn():
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
        return keras_model
        
    #----------------Define automated pipeline-----------------------
    def build_pipeline():
        return Pipeline([
            ('vectorizer', PumpdataVectorizer(station)),
            # Subtracts mean and scales by std on each feature
            ('standarizer', StandardScaler()),
            ('nn', kerasEstimator(build_fcnn(),
                                  EPHOCS,
                                  BATCH_SIZE,
                                  val_split= 0.1))
        ])
    
    # Train
    def train():
        model = build_pipeline()
        model.fit(dataset, labels)
        plot_train(model.named_steps['nn'].history)
        save(model)
    
    #train()
    
    model = load(build_fcnn)
    df = create_pred_dataframe(dataset, station, model)
    
    print(df)
    
    df.iloc[1000:1100].plot()
    plt.show()