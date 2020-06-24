import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input

from plotter import to_dataframes, merge_stations
from data.reader import PickledDataReader
from data.util import string_range

reader = PickledDataReader()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

styles = {
	'selection-wrapper':{
		'display': 'inline-block',
		'width': '32%'
	}
}

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

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
	html.Div([

		html.Div([
			dcc.DatePickerRange(
				id= 'date-selector',
				max_date_allowed= reader.get_latest_date(),
				min_date_allowed= reader.get_earliest_date(),
				initial_visible_month= reader.get_latest_date()
			),
			dcc.RadioItems(
				id= 'radio-timestep',
				options= [
					{'label': 'hours', 'value': 'h'},
					{'label': 'minutes', 'value': 'm'},
					{'label': 'days', 'value': 'd'}
				],
				style={'display': 'flex'}
			)
		], style= {'display': 'flex', 'alignItems': 'center'}),

		dcc.Dropdown(
			id= 'dropdown-station',
			options=[ {'label': i, 'value': i} for i in reader.get_stations()],
			placeholder= 'Velg stasjon...',
			multi= True
		),
		
		dcc.Checklist(
			id= 'checklist-measurments',
			options= [
				{'label': 'quantity (l/s)', 'value': 'q'},
				{'label': 'level (moh)', 'value': 'l'}
			],
			style= {'display':'flex'}
		),
		dcc.Checklist(
			id='checklist-weather',
			options=[
				{'label': 'Inkluder værdata', 'value': 'vaerdata'},
				{'label': 'nedbør (mm)', 'value': 'precipitation (mm)'},
				{'label': 'temperatur (C)', 'value': 'temp (C)'},
			],
			style={'display': 'flex'}
		),
	] + [
		html.Div([
			PeriodSelection(vr, id) for id, vr in {
			'years': reader.get_available_years(),
			'months': string_range(1, 12),
			'days': string_range(1, 31),
			'weeks': range(8)
			}.items()
		], style={'display': 'flex', 'justifyContent': 'space-around'})
	])
])

"""dcc.Graph(id='graph')
@app.callback(
	Output(component_id= 'graph', component_property= 'figure'),
	[Input(component_id= 'dropdown-station', component_property= 'value')]
)
def update_graph(input_value):
	print(input_value)
	df = merge_stations(
		result= to_dataframes(reader.get_data()),
		stations={
			station: (['precipitation (mm)']
			if station== 'vaerdata'
			else ['quantity (l/s)'])
			for station in input_value
		}
	)
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
			'title': 'Sensordata'
		}
	}"""

if __name__ == '__main__':
	app.run_server(debug=True)