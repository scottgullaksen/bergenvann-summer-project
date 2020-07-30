import dash_core_components as dcc
import dash_html_components as html

from project.data import reader
from project.data.util import string_range
from datetime import time

# Re-useable components

def PeriodDropdown(value_range, id):
	return dcc.Dropdown(
		id= f'dropdown-{id}',
		options=[
			{'label': i, 'value': i} for i in value_range
		],
		placeholder= 'alle',
		multi= True
	)

# Components to be used in form

datepicker = dcc.DatePickerRange(
    id= 'date-selector',
    max_date_allowed= reader.get_latest_date(),
    min_date_allowed= reader.get_earliest_date(),
    initial_visible_month= reader.get_latest_date(),
    start_date_placeholder_text= 'Start dato',
    end_date_placeholder_text= 'Slutt dato'
)

# Select years, months, days and weekdays container
dropdown_list = [
    PeriodDropdown(vr, id) for id, vr in {
        'years': reader.get_available_years(),
        'months': string_range(1, 12),
        'days': string_range(1, 31),
        'weekdays': range(1, 8)
    }.items()
]

# Select hours container
rangeslider = dcc.RangeSlider(
    id= 'hours-select',
    marks= {i: time(i).strftime('%H:%M') for i in range(0, 23, 4)},
    value=[0, 23],
    allowCross= False,
    max= 23,
    min=0,
    step=1,
    tooltip={'placement': 'bottomRight'}
)

TimeperiodForm = html.Div(id= 'time-form', children = [
	html.Div([
		html.P(text), component
	])
	for text, component in zip(
        [
            'Velg tidsrom',
            'Filtrer år',
            'Filtrer måneder',
            'Filtrer dager',
            'Filter ukedag',
            'Filtrer klokkeslett'
        ],
        [datepicker] + dropdown_list + [rangeslider]
    )
])