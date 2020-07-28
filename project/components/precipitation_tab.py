import dash_core_components as dcc
import dash_html_components as html

input_lol = dcc.Input(
    id='input-lag',
    type='number',
    min= 0,
    placeholder= 'lag',
    style={'margin': '0% 1%'},
    value= 0
)

PrecipitationForm = html.Div([
    html.P("""
        Her kan du filtere vekk målinger hvor det har regnet mer
        enn en viss mengde før målings-tidspunktet. Resultatet
        viser dermed målinger for "tørre" dager.    
    """),
    html.Div([
        html.Div([
            html.P("""
                Velg grensen for tillat nedbørsmende 
                før en måling:
            """),
            dcc.Input(
                id='input-treshold',
                type='number',
                min= 0,
                placeholder= 'Max nedbør (mm)',
                style={'margin': '0% 1%'},
            )
        ]),

        html.Div([
            html.P("""
                Velg vindu (timer) den satte grensen
                gjelder for:
            """),
            dcc.RangeSlider(
                id= 'rangeslider-wetdays',
                max= 100,
                min= 0,
                step= 1,
                value= [28, 100],
                marks={ 0: '100 t', 28: '72 t', 52: '48 t', 76: '24 t', 100: '0 t'},
                allowCross= False,
                pushable= 1
            )
        ])
    ])
], id= 'prec-form')