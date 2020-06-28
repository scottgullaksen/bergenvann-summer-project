def create_figure(df):
	return {
		'data': [
			dict(
				x= df.index,
				y= df[col],
				mode= 'lines',
				name= col,
				type= 'scatter',
				opacity= 0.7
			) for col in df.columns
		],
		'layout': {
			'title': {
				'text': 'Sensordata',
				'xanchor': 'center',
				'xref': 'paper',
				'y': 0.98
			},
			'transition': {'duration': 500},
			'margin': {'l': 20, 'b': 20, 't': 20, 'r': 10},
			'legend': {'x': 0 , 'yref': 'paper', 'y': 1, 'xref': 'paper', 'bgcolor': 'rgba(0,0,0,0)'}
		}
	}

def resolve_dates(*args):
	import re
	from datetime import datetime as dt
	"""
	If arguments are date strings, convert to dates, otherwise return None
	"""
	return tuple(
		dt.strptime(re.split('T| ', date)[0], '%Y-%m-%d')
		if date is not None else date
		for date in args
	)

def filter_by_hours(df, hour_ints):
	"""Filter date indexed df by the hours (ints) in hour_ints"""
	from datetime import time
	first, last = tuple(map(time, hour_ints))
	if first.hour != 0:
		df = df[first <= df.index.map(lambda d: d.time())]
	if last.hour != 23:
		df = df[df.index.map(lambda d: d.time()) <= last]
	return df