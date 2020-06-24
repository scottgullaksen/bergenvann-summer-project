
import re
import pandas as pd
from datetime import datetime as dt

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
				value='h',
				style={'display': 'flex'}
			)
		], style= {'display': 'flex', 'alignItems': 'center'}),

		dcc.Dropdown(
			id= 'dropdown-station',
			options=[ {'label': i, 'value': i} for i in reader.get_stations()],
			placeholder= 'Velg stasjon...',
			multi= True
		),

		html.Div([
			dcc.Checklist(
				id= 'checklist-pump-meas',
				options= [
					{'label': 'pumpemengde (l/s)', 'value': 'quantity (l/s)'},
					{'label': 'nivå, sump (moh)', 'value': 'level (m)'}
				],
				style= {'display':'flex'}
			),
			dcc.Checklist(
				id= 'checklist-weather-meas',
				options= [
					{'label': 'nedbør (mm)', 'value': 'precipitation (mm)'},
					{'label': 'temperatur (C)', 'value': 'temp (C)'}
				],
				style= {'display':'flex'}
			)
		], style= {'display': 'flex'})

	] + [
		html.Div([
			PeriodSelection(vr, id) for id, vr in {
			'years': reader.get_available_years(),
			'months': string_range(1, 12),
			'days': string_range(1, 31),
			'weekdays': range(8)
			}.items()
		], style={'display': 'flex', 'justifyContent': 'space-around'})
	] + [
		dcc.Graph(id='graph')
	])
])


@app.callback(
	Output(component_id= 'graph', component_property= 'figure'),
	[Input(component_id= 'date-selector', component_property= 'start_date'),
	Input(component_id= 'date-selector', component_property= 'end_date'),
	Input(component_id= 'dropdown-station', component_property= 'value'),
	Input(component_id= 'checklist-pump-meas', component_property= 'value'),
	Input(component_id= 'checklist-weather-meas', component_property= 'value'),
	Input(component_id= 'dropdown-years', component_property= 'value'),
	Input(component_id= 'dropdown-months', component_property= 'value'),
	Input(component_id= 'dropdown-days', component_property= 'value'),
	Input(component_id= 'dropdown-weekdays', component_property= 'value')]
)
def update_graph(date1, date2, stations, pump_meas, weather_meas,
							years, months, days, weekdays):

	if date1 is not None:
		date1 = dt.strptime(re.split('T| ', date1)[0], '%Y-%m-%d')

	if date2 is not None:
		date2 = dt.strptime(re.split('T| ', date2)[0], '%Y-%m-%d')
	# Create appropriate agrument for api call
	print(stations)
	print(pump_meas)
	stations = {
		**({s:pump_meas for s in stations}
		if stations and pump_meas else {})
	}
	if weather_meas: stations['vaerdata'] = weather_meas

	df = merge_stations(
		result= to_dataframes(reader.get_data(
			date1=date1,
			date2=date2,
			years=years,
			months=months,
			days= days,
			weekdays= [] if not weekdays else weekdays
		)),
		stations= stations
	) if stations else pd.DataFrame()

	if df is None: df = pd.DataFrame()

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
	}

if __name__ == '__main__':
	app.run_server(debug=True)