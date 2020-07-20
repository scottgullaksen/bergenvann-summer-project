import time
import numpy as np
import pandas as pd
import joblib
import os
from functools import wraps
from sklearn.model_selection import cross_val_score
from sklearn.metrics import f1_score, make_scorer
import matplotlib.pyplot as plt

from project.modeling.estimators import kerasEstimator

def timeit(func):
    """
    Decorator for timing a fuction.
    Extra return value: delta
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        return result, time.time() - start
    return wrapper

def plot_train(history):
    acc = history.history['mean_absolute_error']
    val_acc = history.history['val_mean_absolute_error']
    loss = history.history['loss']
    val_loss = history.history['val_loss']


    epochs = range(1, len(acc) + 1)

    plt.plot(epochs, acc, '-', label = 'Training acc')
    plt.plot(epochs, val_acc, '-', label = 'Validation acc')
    plt.title('Training and validation accuracy')
    plt.legend()

    plt.figure()

    plt.plot(epochs, loss, '-', label = 'Training loss')
    plt.plot(epochs, val_loss, '-', label = 'Validation loss')
    plt.title('Training and validation loss')
    plt.legend()

    plt.show()
    
def create_pred_dataframe(datapoints, station, model):
    """
    Creates a dataframe with pump values from test_set
    and corresponding estimations from model. Indexed
    by datetime objects. Used for plotting results after
    training keras model.
    """
    
    df = pd.DataFrame({
        'date': [x['date'] for x in datapoints],
        'true values': [x[station]['quantity (l/S)'] for x in datapoints],
        'estimated': model.predict(datapoints).flatten()
    })
    
    df.set_index('date', inplace= True)
    df.sort_index(inplace= True)
    
    return df

def save(model, path_to_dir= None, filename= ''):
    # Create path and make dirs
    parent = path_to_dir or os.path.join(
        os.path.dirname(__file__), 'model_checkpoints'
    )
    if not os.path.exists(parent): os.makedirs(parent)
    
    # Save in respective files
    model.named_steps['nn'].model.save_weights(
        os.path.join(parent, f'{filename}_model.h5')
    )
    model.steps.pop(-1)
    joblib.dump(model,
                os.path.join(parent,
                             f'{filename}_pipeline.pkl'))
    
def load(nn_builder, path_to_dir= None, name= ''):
    
    parent = path_to_dir or os.path.join(
        os.path.dirname(__file__), 'model_checkpoints'
    )
    
    keras_model = nn_builder()
    keras_model.load_weights(
        os.path.join(parent, f'{name}_model.h5'),
    )
    model = joblib.load(
        os.path.join(parent, f'{name}_pipeline.pkl')
    )
    model.steps.append(('nn', kerasEstimator(keras_model)))
    return model

def model_exists(name):
    dirname = os.path.join(
        os.path.dirname(__file__), 'model_checkpoints'
    )
    h5_path = os.path.join(dirname, f'{name}_model.h5')
    pipe_path = os.path.join(dirname, f'{name}_pipeline.pkl')
    return os.path.exists(h5_path) and os.path.exists(pipe_path)

def avg(l): return sum(l)/len(l)