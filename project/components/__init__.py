import dash_core_components as dcc
import dash_html_components as html

from project.components.timetab import TimeperiodForm
from project.components.agg_tab import AggregationForm

def DisplayColumns(df):
	"""
	Creates inline displays of the values for each column
	in the dataframe.
	"""
	return html.Div([
		html.Div(
			id=f'stat-{col}',
			children= [html.H6(f'{col}')] + [
				html.Div(f'{stat}: {df.loc[stat, col]}')
				for stat in df.index
			],
			style={'display': 'inline-block', 'margin': '0% 2%'}
		) for col in df.columns
	])