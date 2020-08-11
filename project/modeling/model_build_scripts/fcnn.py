from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, BatchNormalization, ReLU, Dropout

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from project.modeling.estimators import PumpdataVectorizer, kerasEstimator

#------------Define keras neural net models---------------------------
def gvsrn_nn():
    return Sequential([
        BatchNormalization(
            input_shape=(PumpdataVectorizer.get_vector_len(), )
        ),
        #Dropout(0.5),
        Dense(units= 128),
        ReLU(),
        BatchNormalization(),
        Dropout(0.5),
        Dense(units= 128),
        ReLU(),
        BatchNormalization(),
        #Dropout(0.5),
        Dense(units= 1)
    ])
    
build_fcnn = {
    'Gronneviksoren': gvsrn_nn,
    'WolffsGate': gvsrn_nn,
    'GeorgernesVerft': gvsrn_nn,
    'ThorMohlensVilVite': gvsrn_nn,
    'Nygardstangen': gvsrn_nn
}

if __name__ == "__main__":
    from datetime import datetime as dt
    import matplotlib.pyplot as plt
    import numpy as np
    
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.losses import MeanSquaredError
    from tensorflow.keras.metrics import MeanAbsoluteError
    
    from project.data import reader
    from project.modeling.util import plot_train, create_pred_dataframe, save, load

    #----------------Training parameters-----------------------------------
    EPHOCS = 100
    BATCH_SIZE = 512
    LR = 1e-4
    INPUT_SIZE = (125,) # Constant
    TEST_SIZE = 1000
    
    #-------------------Define datasets------------------------------------
    # Load data
    station = 'Nygardstangen'
    save_name = station

    # These dates are picked based on available weather data
    """dataset = sorted([
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
    ], key= lambda x: x['date'])"""
    
    # For station: GeorgenesVerft
    dataset = sorted([
        x for x in reader.get_data(
            dt(2012, 10, 25, 11),
            dt(2012, 11, 30, 11),
            how= 'stream'
        )
        if station in x
    ] + [
        x for x in reader.get_data(
            dt(2012, 12, 11, 11),
            dt(2015, 1, 6, 7),
            how= 'stream'
        )
        if station in x
    ] + [
        x for x in reader.get_data(
            dt(2015, 1, 13, 12),
            how= 'stream'
        )
        if station in x
    ], key= lambda x: x['date'])
    
    labels = np.array([x[station]['quantity (l/s)'] for x in dataset])
    
    # Train-test splits
    X_train = dataset[:-TEST_SIZE]
    Y_train = labels[:-TEST_SIZE]
    
    X_test = dataset[-TEST_SIZE:]
    Y_test = labels[-TEST_SIZE:]
    
    #----------------Train and eval scripts---------
    def train():
        # Compile keras model to ready for training
        keras_model = build_fcnn[station]()
        keras_model.compile(
            optimizer= Adam(learning_rate= LR),
            loss= MeanSquaredError(),
            metrics= [MeanAbsoluteError()]
        )
        keras_model.summary()
        
        # Define automated pipeline
        model = Pipeline([
            ('vectorizer', PumpdataVectorizer(station)),
            # Subtracts mean and scales by std on each feature
            ('standarizer', StandardScaler()),
            ('nn', kerasEstimator(keras_model,
                                  EPHOCS,
                                  BATCH_SIZE,
                                  val_split= 0.07))
        ])

        model.fit(X_train, Y_train)

        plot_train(model.named_steps['nn'].history)

        save(model, filename=save_name)
    
    def evaluate():
        # So you don't have to retrain every time you want to evaluate
        model = load(build_fcnn, name=save_name)
        
        model.named_steps['nn'].model.compile(
            optimizer= Adam(learning_rate= LR),
            loss= MeanSquaredError(),
            metrics= [MeanAbsoluteError()]
        )

        # Get loss(mse) and mae
        score = model.score(X_test, Y_test)
        print(score)

        # Plot predictions vs real values
        df = create_pred_dataframe(X_test, station, model)
        df.plot()
        plt.show()

    train()
    evaluate()