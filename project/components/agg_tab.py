import dash_core_components as dcc
import dash_html_components as html

def AggregationDropdown(id: str):
	"""Dropdown menu for aggregation methods"""
	return dcc.Dropdown(
		id= f'dropdown-{id}-agg',
		placeholder='metode',
		options=[
			{'label': 'gjennomsnitt', 'value': 'mean'},
			{'label': 'max', 'value': 'max'},
			{'label': 'min', 'value': 'min'},
			{'label': 'sum', 'value': 'sum'},
		]
	)

# Each component is a text and a dropdown
dropdown_components = [
    html.Div([
        html.P(text), component
    ])
    for text, component in zip(
        [
            'År', 'Måneder', 'Dager', 'Timer'
        ],
        [
            AggregationDropdown(id)
            for id in ['years', 'months', 'days', 'hours']
        ]
    )
]

AggregationForm = html.Div([
    html.P(
        'Slå sammen timer, dager, måneder og/eller år ved å velge en aggregeringsmetode.'
    ),
    # Devide components in two divs, to get column like structure
    html.Div(dropdown_components[:2]),
    html.Div(dropdown_components[2:])
], id= 'agg-form')