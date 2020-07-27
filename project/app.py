import re
import pandas as pd
from datetime import time, datetime
import json

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input, State

from project.data import reader
from project.data.util import string_range, merge_stations, stream_to_dataframe, PUMPSTATIONS
from project.util import *
from project.modeling import add_predictions, get_predictions
from project.components import DisplayColumns, AggregationForm, TimeperiodForm
import numpy as np


reader = reader()

external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    
    html.H4('Bergen Vann Pumpedata'),
    
    html.H5('Analyseverktøy'),
    
    html.Div(className= 'paper', children= dbc.Tabs([
        
        dbc.Tab(label= 'Datakilder', children= [
            # Dropdown for selecting pump station to display in graph
            dcc.Dropdown(
                id= 'dropdown-station',
                options=[ {'label': i, 'value': i} for i in reader.get_stations()],
                placeholder= 'Velg stasjon...',
                multi= True
            ),
            # Checkbox container for selecting measurments to be shown in graph
            html.Div([
                dbc.Fade(
                    dcc.Checklist(
                        id= 'checklist-pump-meas',
                        options= [
                            {'label': 'pumpemengde (l/s)', 'value': 'quantity (l/s)'},
                            {'label': 'nivå, sump (moh)', 'value': 'level (m)'}
                        ]
                    ),
                    id= 'fade-pump',
                    is_in= False
                ),
                dbc.Fade(
                    dcc.Checklist(
                        id= 'checklist-weather-meas',
                        options= [
                            {'label': 'nedbør (mm)', 'value': 'precipitation (mm)'},
                            {'label': 'temperatur (C)', 'value': 'temp (C)'}
                        ]
                    ),
                    id= 'fade-weather',
                    is_in= False
                )
            ], id= 'meas-select')
        ]),
        # Filter wetdays components
        dbc.Tab(label= 'Nedbørs-filter', children= [
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
        ]),
        
        
        # Date window selection for data query
        dbc.Tab(
            label= 'Tidsvindu',
            children= TimeperiodForm
        ),
        
        dbc.Tab(
            label= 'Aggregering',
            children= AggregationForm
        )
    ])),

    dcc.Graph(id='graph', className= 'paper'),

    # Container for conditional render of statistics
    html.Div(id= 'statistics', className= 'paper')
], id= 'dash-dev-entry')

@app.callback(
    [Output('fade-pump', 'is_in'), Output('fade-pump', 'style')],
    [Input('dropdown-station', 'value')]
)
def fade(dropdown_selesctions):
    is_in = (dropdown_selesctions != None and
            any(s in dropdown_selesctions for s in PUMPSTATIONS))
    style = {} if is_in else {'display': 'none'}
    return is_in, style

@app.callback(
    Output('fade-weather', 'is_in'),
    [Input('dropdown-station', 'value')]
)
def fade(dropdown_selesctions):
    return True
    return (dropdown_selesctions != None and
            any('florida' in ds for ds in dropdown_selesctions))


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
    
    # Used to filter dataframe before display
    Input('hours-select', 'value'),
    Input('dropdown-hours-agg', 'value'),
    Input('dropdown-days-agg', 'value'),
    Input('dropdown-months-agg', 'value'),
    Input('dropdown-years-agg', 'value')
])
def update_graph(start_date, end_date, years, months, days, weekdays, # Used as get_data args
                 stations, pump_meas, weather_meas, treshold, window_size, lag,
                 hour_pair, hour_agg_val, days_agg_val, months_agg_val, years_agg_val):

    start_date, end_date = resolve_dates(start_date, end_date)
    
    result = sorted(
        reader.get_data(start_date, end_date, years, months, days,
                        weekdays= weekdays or [], how= 'stream'),
        key= lambda x: x['date']
    )
    
    df = create_dataframe(result, stations, pump_meas, weather_meas)
    
    df, stats = manipulate_dataframe(df, hour_pair, treshold, window_size, lag,
                                     hour_agg_val, days_agg_val, months_agg_val, years_agg_val)
    
    return create_figure(df), DisplayColumns(stats)

def create_dataframe(datapoints, stations, pump_meas, weather_meas):
    
    # Create appropriate argument required by merge
    stations = {
        **({s:(pump_meas + ['estimated']) for s in stations}
        if stations and pump_meas else {})
    }
        
    if weather_meas: stations['florida_sentrum'] = weather_meas
    
    return stream_to_dataframe(
        add_predictions(datapoints, stations.keys()),
        stations
    )

def manipulate_dataframe(df, hour_pair, treshold, window_size, lag,
                         hour_agg_val, days_agg_val, months_agg_val, years_agg_val):
    # Filter as specified
    df = filter_by_hours(df, hour_pair)
    
        
    if treshold:
        df = filter_wet_days(df, window_size[0], treshold, lag)
    
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