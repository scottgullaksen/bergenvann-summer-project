import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input

from plotter import to_dataframes, merge_stations
from data.reader import PickledDataReader

reader = PickledDataReader()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

styles = {

}

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
				style={'dislay': 'inline-block'}
			)
		],
		style= { 'display': 'inline-block', 'width': '32%'}),

		html.Div([
			dcc.Dropdown(
				id='dropdown-station',
				options=[ {'label': i, 'value': i} for i in reader.get_stations()],
				multi= True,
			),

		])
	],
	style={'float': 'right', 'display': 'inline-block'}),
	dcc.Graph(id='graph')
])

@app.callback([
	Output(component_id= 'graph', component_property= 'figure'),
	[Input(component_id= 'station-dropdown', component_property= 'value')]
])
def update_graph(input_value):
	return {
		'data': [
			merge_stations(
				result= to_dataframes(reader.get_data()),
				stations={
					station: (['precipitation (mm)']
					if station== 'vaerdata'
					else ['quantity (l/s)'])
					for station in input_value
				}
			)
		],
		'layout': {
			'title': 'Sensordata'
		}
	}

if __name__ == '__main__':
	app.run_server(debug=True)