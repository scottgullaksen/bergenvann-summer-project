import time
import numpy as np
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

@timeit
def train(model, x, y, cv= 5):
	scores = cross_val_score(model, x, y, cv= cv, scoring= 'f1_micro')
	model['nn'].val_split = 1 / cv
	model.fit(x, y)
	return scores

def plot_train(history):
	acc = history.history['accuracy']
	val_acc = history.history['val_accuracy']
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

def evaluate(model, X_train, y_train, X_test, y_test):
	"""
	Compute
	- final test loss & acc
	- K-fold cross validation f1-score
	- Fitting time
	- loss and acc plot for training and validation
	"""
	scores, delta = train(model, X_train, y_train)

	loss, acc = model.score(X_test, y_test)

	print('Test accuracy: {}'.format(acc))
	print('Test loss: {}'.format(loss))
	print('f1 score: {}'.format(scores.mean()))
	print('Total fit time: {:0.2f} seconds'.format(delta))

	plot_train(model['nn'].history)

def avg(l): return sum(l)/len(l)