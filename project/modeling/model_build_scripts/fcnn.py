from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, BatchNormalization, ReLU, Dropout

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from project.modeling.estimators import PumpdataVectorizer, kerasEstimator

#------------Define keras neural net model---------------------------
def build_fcnn():
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

if __name__ == "__main__":
    from datetime import datetime as dt
    import matplotlib.pyplot as plt
    
    from keras.optimizers import Adam
    from keras.losses import MeanSquaredError
    from keras.metrics import MeanAbsoluteError
    
    from project.data import reader
    from project.modeling.util import plot_train, create_pred_dataframe, save, load

    #----------------Training parameters-----------------------------------
    EPHOCS = 100
    BATCH_SIZE = 512
    LR = 1e-4
    INPUT_SIZE = (125,) # Constant
    TEST_SIZE = 5000
    
    #-------------------Define datasets------------------------------------
    # Load data
    station = 'Gronneviksoren'
    save_name = station

    dataset = sorted([
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
    ], key= lambda x: x['date'])
    
    labels = [x[station]['quantity (l/s)'] for x in dataset]
    
    # Train-test splits
    X_train = dataset[:-TEST_SIZE]
    Y_train = labels[:-TEST_SIZE]
    
    X_test = dataset[-TEST_SIZE:]
    Y_test = labels[-TEST_SIZE:]
    
    #----------------Train and eval scripts---------
    def train():
        # Compile keras model to ready for training
        keras_model = build_fcnn()
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

        save(model, name=save_name)
    
    def evaluate():
        # So you don't have to retrain every time you want to evaluate
        model = load(build_fcnn, name=save_names)

        # Get loss(mse) and mae
        score = model.score(X_test, Y_test)
        print(score)

        # Plot predictions vs real values
        df = create_pred_dataframe(X_test, station, model)
        df.plot()
        plt.show()

    #train()
    evaluate()