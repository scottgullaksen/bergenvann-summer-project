if __name__ == "__main__":
    from datetime import datetime as dt
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
    from project.modeling.util import plot_train, create_pred_dataframe, save, load
    
    #-------------------Load dataset------------------------------------
    reader = PickledDataReader()
    station = 'Gronneviksoren'
    #station = 'GeorgernesVerft'
    
    dataset = [
        x for x in reader.get_data(
            dt(2010, 4, 1),
            dt(2011, 3, 13),
            how= 'stream'
        )
        if station in x
    ] + [
        x for x in reader.get_data(
            dt(2011, 4, 6),
            how= 'stream'
        )
        if station in x
    ]

    dataset.sort(key= lambda x: x['date'])  # Sort on date, ascending
    labels = [x[station]['quantity (l/s)'] for x in dataset]
    
    #----------------Training parameters-----------------------------------
    EPHOCS = 100
    BATCH_SIZE = 512
    LR = 1e-4
    INPUT_SIZE = (125,) # Constant
    TEST_SIZE = 5000
    
    #------------Define keras neural net model---------------------------
    def build_fcnn():
        keras_model = Sequential([
            BatchNormalization(input_shape=INPUT_SIZE),
            Dropout(0.5),
            Dense(units= 128),
            ReLU(),
            BatchNormalization(),
            Dropout(0.5),
            Dense(units= 128),
            ReLU(),
            BatchNormalization(),
            Dropout(0.5),
            Dense(units= 1)
        ])

        keras_model.compile(
            optimizer= Adam(learning_rate= LR),
            loss= MeanSquaredError(),
            metrics= [MeanAbsoluteError()]
        )
        keras_model.summary()
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
                                  val_split= 0.07))
        ])

    #------------------Train and evaluate------------------------
    def train():
        X_train = dataset[:-TEST_SIZE]
        Y_train = labels[:-TEST_SIZE]
        
        model = build_pipeline()
        model.fit(X_train, Y_train)
        
        plot_train(model.named_steps['nn'].history)
        
        save(model, filename=station)

    def evaluate():
        X_test = dataset[-TEST_SIZE:]
        Y_test = labels[-TEST_SIZE:]
        
        # So you don't have to retrain every time you want to evaluate
        model = load(build_fcnn, filename=station)
        
        # Get loss(mse) and mae
        score = model.score(X_test, Y_test)
        print(score)
        
        # Plot predictions vs real values
        df = create_pred_dataframe(X_test, station, model)
        df.plot()
        plt.show()
        
    train()
    evaluate()