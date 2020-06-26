import dash_core_components as dcc
import dash_html_components as html

def PeriodSelection(value_range, id):
	return html.Div([

		dcc.Dropdown(
			id= f'dropdown-{id}',
			options=[
				{'label': i, 'value': i} for i in value_range
			],
			placeholder= id,
			multi= True
		),

		dcc.Dropdown(
			id= f'dropdown-{id}-agg',
			placeholder='Slå sammen',
			options=[
				{'label': 'mean', 'value': 'mean'},
				{'label': 'max', 'value': 'max'},
				{'label': 'min', 'value': 'min'},
				{'label': 'sum', 'value': 'sum'},
			]
		)
	], style= {'width': '20%'})

def KeyStatistics(df):
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