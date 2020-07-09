import time
import numpy as np
import pandas as pd
import joblib
from functools import wraps
from sklearn.model_selection import cross_val_score
from sklearn.metrics import f1_score, make_scorer
import matplotlib.pyplot as plt

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

def numericalize(l):
    """
    Takes a list of labels, e.g. strings, and maps
    them to a unique integer.
    Example:
    'A', 'B' -> 0, 1
    """
    d = dict([(y,x) for x,y in enumerate(sorted(set(l)))])
    return np.array([d[x] for x in l])

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
    
def create_pred_dataframe(test_set, station, model):
    """
    Creates a dataframe with pump values from test_set
    and corresponding estimations from model. Indexed
    by datetime objects.
    """
    
    df = pd.DataFrame({
        'date': [x['date'] for x in test_set],
        'true values': [x[station]['quantity (l/s)'] for x in test_set],
        'estimated': model.predict(test_set).flatten()
    })
    
    df.set_index('date', inplace= True)
    df.sort_index(inplace= True)
    
    return df

def save(model):
    model.named_steps['nn'].model.save_weights('nn_model.h5')
    model.steps.pop(-1)
    joblib.dump(model, 'pipeline.pkl')
    
def load(nn_builder):
    from project.modeling.estimators import kerasEstimator
    keras_model = nn_builder()
    keras_model.load_weights('nn_model.h5')
    model = joblib.load('pipeline.pkl')
    model.steps.append(('nn', kerasEstimator(keras_model)))
    return model

def avg(l): return sum(l)/len(l)