import re
import pandas as pd
from datetime import time
import json

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input

from data.reader import PickledDataReader
from data.util import string_range, merge_stations

from components import PeriodSelection, DisplayColumns, AggregationDropdown
from util import aggregate_days, aggregate_hours, aggregate_months, aggregate_years, create_figure, filter_by_hours, filter_wet_days, resolve_dates

reader = PickledDataReader()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div([

        dcc.Dropdown(
            id= 'dropdown-station',
            options=[ {'label': i, 'value': i} for i in reader.get_stations()],
            placeholder= 'Velg stasjon...',
            multi= True
        ),

        # Container for selecting measurments to be shown in graph
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
            ),
            dcc.Input(
                id='input-treshold',
                type='number',
                min= 0,
                placeholder= 'Max nedbør (mm)',
                style={'margin': '0% 1%'},
            ),
            html.Div(dcc.RangeSlider(
                id= 'rangeslider-wetdays',
                max= 5,
                min= 1,
                step= 1,
                value= [1],
                marks={  i: str(i) for i in range(1, 6) }
            ), style= { 'width': '20%'}),
            dcc.Input(
                id='input-lag',
                type='number',
                min= 0,
                placeholder= 'lag',
                style={'margin': '0% 1%'},
                value= 0
            )
        ], style= {'display': 'flex'}),

        dcc.DatePickerRange(
            id= 'date-selector',
            max_date_allowed= reader.get_latest_date(),
            min_date_allowed= reader.get_earliest_date(),
            initial_visible_month= reader.get_latest_date(),
            style= { 'borderStyle': 'none'}  # Doesn't work
        ),

        # Select years, months, days and weekdays container
        html.Div([
            PeriodSelection(vr, id) for id, vr in {
            'years': reader.get_available_years(),
            'months': string_range(1, 12),
            'days': string_range(1, 31),
            'weekdays': range(8)
            }.items()
        ], style={'display': 'flex', 'justifyContent': 'space-around'}),

        # Select hours container
        html.Div([
            html.Div(dcc.RangeSlider(
                id= 'hours-select',
                marks= {i: time(i).strftime('%H:%M') for i in range(0, 23, 4)},
                value=[0, 23],
                allowCross= False,
                max= 23,
                min=0,
                step=1,
                tooltip={'placement': 'bottomRight'}
            ), style={'display': 'inline-block', 'width': '80%'}),
            html.Div(
                AggregationDropdown('hours'),
                style={'display': 'inline-block', 'width': '18%'}
            )
        ]),

        dcc.Graph(id='graph'),

        # Container for conditional render of statistics
        html.Div( id= 'statistics'),

        # state - hidden
        html.Div(id= 'state-result', style={'display': 'none'}),
        html.Div(id= 'state-merged-df', style={'display': 'none'})
    ])
])

@app.callback(
    Output('state-result', 'children'),[
    Input('date-selector', 'start_date'),
    Input('date-selector', 'end_date'),
    Input('dropdown-years', 'value'),
    Input('dropdown-months', 'value'),
    Input('dropdown-days', 'value'),
    Input('dropdown-weekdays', 'value')
])
def update_result(start_date, end_date, years, months, days, weekdays):

    start_date, end_date = resolve_dates(start_date, end_date)

    dict_of_df = reader.get_data(start_date, end_date, years, months, days,
                        weekdays= [] if not weekdays else weekdays)
    return json.dumps({
        station: df.to_json(date_format='iso', orient='split')
        for station, df in dict_of_df.items()
    })

@app.callback(
    Output('state-merged-df', 'children'), [
    Input('dropdown-station', 'value'),
    Input('checklist-pump-meas', 'value'),
    Input('checklist-weather-meas', 'value'),
    Input('state-result', 'children'),
    Input('input-treshold', 'value'),
    Input('rangeslider-wetdays', 'value'),
    Input('input-lag', 'value')
])
def update_merged_df(stations, pump_meas, weather_meas, state, treshold, window_size, lag):

    # Create appropriate argument required by merge
    stations = {
        **({s:pump_meas for s in stations}
        if stations and pump_meas else {})
    }
    if weather_meas: stations['vaerdata'] = weather_meas
    
    result = {  # Read from jsonified state
        station: pd.read_json(jsond_df, orient= 'split')
        for station, jsond_df in json.loads(state).items()
    }
    
    if treshold:
        result = filter_wet_days(result, window_size[0], treshold, lag)
    
    df = merge_stations(result,stations) if stations else None

    if df is None:
        raise dash.exceptions.PreventUpdate(
            'No stations/measurements specified, abort update'
        )

    return df.to_json(date_format='iso', orient='split')

@app.callback(
    [Output('graph', 'figure'), Output('statistics', 'children')],[
    Input('state-merged-df','children'),
    Input('hours-select', 'value'),
    Input('dropdown-hours-agg', 'value'),
    Input('dropdown-days-agg', 'value'),
    Input('dropdown-months-agg', 'value'),
    Input('dropdown-years-agg', 'value'),]
)
def update_graph(jsonified_df, hour_pair, hour_agg_val, days_agg_val, months_agg_val, years_agg_val):
    if jsonified_df is None:
        raise dash.exceptions.PreventUpdate(
            'First time trough callback chain - no graph render'
        )

    # To be shown in graph
    df = pd.read_json(jsonified_df, orient='split')

    # Filter as specified
    df = filter_by_hours(df, hour_pair)
    
    # To be shown beneath graph
    stats = df.agg({
        col: ['mean', 'max', 'min', 'median', 'sum', 'std']
        for col in df.columns
    })
    
    # Repeating code here, fix later
    if hour_agg_val != None:
        df = aggregate_hours(df, hour_agg_val)
    
    if days_agg_val != None:
        df = aggregate_days(df, days_agg_val)
    
    if months_agg_val != None:
        df = aggregate_months(df, months_agg_val)
    
    if years_agg_val != None:
        df = aggregate_years(df, years_agg_val)

    return create_figure(df), DisplayColumns(stats)

if __name__ == '__main__':
    app.run_server(debug=True)