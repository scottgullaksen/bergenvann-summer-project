import dash_core_components as dcc
import dash_html_components as html

from project.data import reader

DataSourceForm = html.Div([
    # Dropdown for selecting pump station to display in graph
    dcc.Dropdown(
        id= 'dropdown-station',
        options=[ {'label': i, 'value': i} for i in reader.get_stations()],
        placeholder= 'Velg stasjon...',
        multi= True
    ),

    # Checkbox container for selecting measurments to be shown in graph
    html.Div([
        # So contents can be hidden if pumpstations not selected
        html.Div(
            id= 'hide-pump',
            children= dcc.Checklist(
                id= 'checklist-pump-meas',
                options= [
                    {'label': 'pumpemengde (l/s)', 'value': 'quantity (l/s)'},
                    {'label': 'nivå, sump (moh)', 'value': 'level (m)'},
                    {'label': 'estimat', 'value': 'estimated' }
                ]
            ),
        ),
        # To enable hiding - same as above
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
])