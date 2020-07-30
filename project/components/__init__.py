import dash_core_components as dcc
import dash_html_components as html

from project.components.timetab import TimeperiodForm
from project.components.agg_tab import AggregationForm
from project.components.precipitation_tab import PrecipitationForm
from project.components.datasource_tab import DataSourceForm

def DisplayColumns(df):
    """
    Creates inline displays of the values for each column
    in the dataframe.
    """
    return [
        html.Div(
            id=f'stat-{col}',
            className= 'paper',
            children= [html.H6(f'{col}')] + [
                html.Div(f'{stat}: {df.loc[stat, col]}')
                for stat in df.index
            ],
            style={'display': 'inline-block'}
        ) for col in df.columns
    ]