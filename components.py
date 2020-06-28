import dash_core_components as dcc
import dash_html_components as html

def AggregationDropdown(id: str):
	"""Dropdown menu for aggregation methods"""
	return dcc.Dropdown(
		id= f'dropdown-{id}-agg',
		placeholder='Slå sammen',
		options=[
			{'label': 'mean', 'value': 'mean'},
			{'label': 'max', 'value': 'max'},
			{'label': 'min', 'value': 'min'},
			{'label': 'sum', 'value': 'sum'},
		]
	)

def PeriodSelection(value_range, id):
	"""
	Creates a vertical stack of two dropdown menus.
	Top one holds the range of values for selection
	and bottom one choose aggregation method for
	the selected values
	"""
	return html.Div([
		dcc.Dropdown(
			id= f'dropdown-{id}',
			options=[
				{'label': i, 'value': i} for i in value_range
			],
			placeholder= id,
			multi= True
		),
		AggregationDropdown(id)
	], style= {'width': '20%'})

def DisplayColumns(df):
	"""
	Creates inline displays of the values for each column
	in the dataframe.
	"""
	return html.Div([
		html.Div(
			id=f'stat-{col}',
			children= [html.H6(f'{col}')] + [
				html.Div(f'{stat}: {df.loc[stat, col]}')
				for stat in df.index
			],
			style={'display': 'inline-block', 'margin': '0% 2%'}
		) for col in df.columns
	])