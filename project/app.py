import re
import pandas as pd
from datetime import time, datetime
import json

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input

from project.data import reader
from project.data.util import string_range, merge_stations, stream_to_dataframe
from project.util import *
from project.modeling import add_predictions, get_predictions
from project.components import PeriodSelection, DisplayColumns, AggregationDropdown
import numpy as np


reader = reader()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div([

        # Dropdown for selecting pump station to display in graph
        dcc.Dropdown(
            id= 'dropdown-station',
            options=[ {'label': i, 'value': i} for i in reader.get_stations()],
            placeholder= 'Velg stasjon...',
            multi= True
        ),

        # Checkbox container for selecting measurments to be shown in graph
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
            # Filter wetdays components
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
        
        # Checkbox container for including tide & snow data in graph
        html.Div([
            dcc.Checklist(
                id= 'checklist-tide',
                options=[
                    {'label': 'Tidevann', 'value': 'level (cm)'}
                ]
            ),
            dcc.Checklist(
                id= 'checklist-snow',
                options=[
                    {'label': 'Snødybde', 'value': 'snodybde (cm)'}
                ]
            )
        ], style= {'display': 'flex'}),

        # Date window selection for data query
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
    #Output('state-result', 'children'),
    [Output('graph', 'figure'), Output('statistics', 'children')],[
        
    # Parameters for data query
    Input('date-selector', 'start_date'),
    Input('date-selector', 'end_date'),
    Input('dropdown-years', 'value'),
    Input('dropdown-months', 'value'),
    Input('dropdown-days', 'value'),
    Input('dropdown-weekdays', 'value'),
    
    # These determine what to display from result
    #Input('state-result', 'children'),
    Input('dropdown-station', 'value'),
    Input('checklist-pump-meas', 'value'),
    Input('checklist-weather-meas', 'value'),
    Input('input-treshold', 'value'),
    Input('rangeslider-wetdays', 'value'),
    Input('input-lag', 'value'),
    Input('checklist-snow', 'value'),
    Input('checklist-tide', 'value'),
    
    # Used to filter dataframe before display
    Input('hours-select', 'value'),
    Input('dropdown-hours-agg', 'value'),
    Input('dropdown-days-agg', 'value'),
    Input('dropdown-months-agg', 'value'),
    Input('dropdown-years-agg', 'value')
])
def update_graph(start_date, end_date, years, months, days, weekdays, # Used as get_data args
                 stations, pump_meas, weather_meas, treshold, window_size, lag, snow, tide,
                 hour_pair, hour_agg_val, days_agg_val, months_agg_val, years_agg_val):

    start_date, end_date = resolve_dates(start_date, end_date)
    
    result = sorted(
        reader.get_data(start_date, end_date, years, months, days,
                        weekdays= weekdays or [], how= 'stream'),
        key= lambda x: x['date']
    )
    
    df = create_dataframe(result, stations, pump_meas, weather_meas,
                          treshold, window_size, lag, snow, tide)
    
    df, stats = manipulate_dataframe(df, hour_pair, hour_agg_val, days_agg_val,
                              months_agg_val, years_agg_val)
    
    return create_figure(df), DisplayColumns(stats)


def create_dataframe(datapoints, stations, pump_meas, weather_meas,
                     treshold, window_size, lag, snow, tide):
    
    # Create appropriate argument required by merge
    stations = {
        **({s:(pump_meas + ['estimated']) for s in stations}
        if stations and pump_meas else {})
    }
        
    if weather_meas: stations['florida_sentrum'] = weather_meas
    if snow: stations['snodybde'] = snow
    if tide: stations['tidevannsdata'] = tide
    
    df = stream_to_dataframe(
        add_predictions(datapoints, stations.keys()),
        stations
    )
    
    if treshold:
        result = filter_wet_days(result, window_size[0], treshold, lag)

    return df

def manipulate_dataframe(df, hour_pair, hour_agg_val, days_agg_val,
                        months_agg_val, years_agg_val):
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

    #return create_figure(df), DisplayColumns(stats)
    return df, stats

if __name__ == '__main__':
    app.run_server(debug= True)