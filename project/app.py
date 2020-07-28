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
from project.components import *
import numpy as np


reader = reader()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    
    html.H4('Bergen Vann Pumpedata'),
    
    html.H5('Analyseverktøy'),
    
    html.Div(
        className= 'paper',
        children= dcc.Tabs(
            className= 'custom-tabs-container',
            parent_className= 'custom-tabs',
            children= [
            dcc.Tab(
                label= 'Datakilder',
                className= 'custom-tab',
                selected_className='custom-tab--selected',
                children= [
                    # Dropdown for selecting pump station to display in graph
                    dcc.Dropdown(
                        id= 'dropdown-station',
                        options=[ {'label': i, 'value': i} for i in reader.get_stations()],
                        placeholder= 'Velg stasjon...',
                        multi= True
                    ),
                    # Checkbox container for selecting measurments to be shown in graph
                    html.Div([
                        html.Div(
                            id= 'hide-pump',
                            children= dcc.Checklist(
                                id= 'checklist-pump-meas',
                                options= [
                                    {'label': 'pumpemengde (l/s)', 'value': 'quantity (l/s)'},
                                    {'label': 'nivå, sump (moh)', 'value': 'level (m)'}
                                ]
                            ),
                        ),
                        html.Div(
                            id= 'hide-weather',
                            children= dcc.Checklist(
                                id= 'checklist-weather-meas',
                                options= [
                                    {'label': 'nedbør (mm)', 'value': 'precipitation (mm)'},
                                    {'label': 'temperatur (C)', 'value': 'temp (C)'}
                                ]
                            )
                        )
                    ], id= 'meas-select')
                ]
            ),

            # Filter wetdays components
            dcc.Tab(
                label= 'Nedbørs-filter',
                className= 'custom-tab',
                selected_className='custom-tab--selected',
                children= PrecipitationForm
            ),

            # Date window selection for data query
            dcc.Tab(
                label= 'Tidsvindu',
                className= 'custom-tab',
                selected_className='custom-tab--selected',
                children= TimeperiodForm
            ),

            dcc.Tab(
                label= 'Aggregering',
                className= 'custom-tab',
                selected_className='custom-tab--selected',
                children= AggregationForm
            )
    ])),

    dcc.Graph(id='graph', className= 'paper'),

    # Container for conditional render of statistics
    html.Div(id= 'statistics', className= 'paper')
], id= 'dash-dev-entry')

@app.callback(
    Output('hide-pump', 'style'),
    [Input('dropdown-station', 'value')]
)
def hide(dropdown_selesctions):
    is_in = (dropdown_selesctions != None and
            any(s in dropdown_selesctions for s in PUMPSTATIONS))
    style = {} if is_in else {'display': 'none'}
    return style

@app.callback(
    Output('hide-weather', 'style'),
    [Input('dropdown-station', 'value')]
)
def hide(dropdown_selesctions):
    is_in = (dropdown_selesctions != None and
            any('florida' in ds for ds in dropdown_selesctions))
    style = {} if is_in else {'display': 'none'}
    return style

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
    
    # Used to filter dataframe before display
    Input('hours-select', 'value'),
    Input('dropdown-hours-agg', 'value'),
    Input('dropdown-days-agg', 'value'),
    Input('dropdown-months-agg', 'value'),
    Input('dropdown-years-agg', 'value')
])
def update_graph(start_date, end_date, years, months, days, weekdays, # Used as get_data args
                 stations, pump_meas, weather_meas, treshold, window,
                 hour_pair, hour_agg_val, days_agg_val, months_agg_val, years_agg_val):

    start_date, end_date = resolve_dates(start_date, end_date)
    
    result = sorted(
        reader.get_data(start_date, end_date, years, months, days,
                        weekdays= weekdays or [], how= 'stream'),
        key= lambda x: x['date']
    )
    
    df = create_dataframe(result, stations, pump_meas,
                          weather_meas, treshold, window)
    
    df, stats = manipulate_dataframe(df, hour_pair, hour_agg_val, days_agg_val,
                                     months_agg_val, years_agg_val)
    
    return create_figure(df), DisplayColumns(stats)

def create_dataframe(datapoints, stations, pump_meas,
                     weather_meas, treshold, window):
    
    if treshold:
        datapoints = filter_wet_days(datapoints, window, treshold)
    
    # Define data to include in dataframe
    stations = stations or []
    df_data = {}
    
    for s in stations:
        if s in PUMPSTATIONS and pump_meas:
            df_data[s] = pump_meas + ['estimated']
        elif 'florida' in s and weather_meas:
            df_data[s] = weather_meas
        elif s == 'snodybde':
            df_data[s] = ['snodybde (cm)']
        elif s == 'tidevannsdata':
            df_data[s] = ['level (cm)']
    
    return stream_to_dataframe(
        add_predictions(datapoints, df_data.keys()),
        df_data
    )

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