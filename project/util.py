import pandas as pd

def create_figure(df):
    return {
        'data': [
            dict(
                x= df.index,
                y= df[col],
                mode= 'lines',
                name= col,
                type= 'scatter',
                opacity= 0.7
            ) for col in df.columns
        ],
        'layout': {
            'title': {
                'text': 'Sensordata',
                'xanchor': 'center',
                'xref': 'paper',
                'y': 0.98
            },
            'transition': {'duration': 500},
            'margin': {'l': 20, 'b': 20, 't': 20, 'r': 10},
            'legend': {'x': 0 , 'yref': 'paper', 'y': 1, 'xref': 'paper', 'bgcolor': 'rgba(0,0,0,0)'}
        }
    }

def resolve_dates(*args):
    import re
    from datetime import datetime as dt
    """
    If arguments are date strings, convert to dates, otherwise return None
    """
    return tuple(
        dt.strptime(re.split('T| ', date)[0], '%Y-%m-%d')
        if date is not None else date
        for date in args
    )

def filter_by_hours(df, hour_ints):
    """Filter date indexed df by the hours (ints) in hour_ints"""
    from datetime import time
    first, last = tuple(map(time, hour_ints))
    if first.hour != 0:
        df = df = df[first <= df.index.map(lambda d: d.time())]
    if last.hour != 23:
        df = df[df.index.map(lambda d: d.time()) <= last]
    return df  # Could also use df.between_time(start_time, end_time), faster?

def aggregate_hours(df: pd.DataFrame, method: str = 'mean'):
    """Aggregate specified hours by method (mean, max, min or median)"""
    df = df.groupby(df.index.date).agg({ col: [method] for col in df.columns })
    df.index = pd.to_datetime(df.index)
    df.columns = df.columns.droplevel(1)
    return df

def aggregate_days(df: pd.DataFrame, method: str = 'mean'):
    """Aggregate days of the month by method, e.g. mean"""
    df =  df.groupby([pd.Grouper(freq='MS'), df.index.hour]).agg(
        { col: [method] for col in df.columns}
    )
    df.index = df.index.map( lambda m: m[0].replace(hour=m[1]))
    df.columns = df.columns.droplevel(1)
    return df

def aggregate_months(df: pd.DataFrame, method: str = 'mean'):
    """Aggregate months of the year by methof, e.g. sum"""
    df =  df.groupby([pd.Grouper(freq='Y'), df.index.day, df.index.hour]).agg(
        { col: [method] for col in df.columns}
    )
    df.index = df.index.map( lambda m: m[0].replace(day= m[1], hour=m[2]) )
    df.columns = df.columns.droplevel(1)
    return df


def aggregate_years(df: pd.DataFrame, method: str = 'mean'):
    from datetime import datetime as dt
    """Aggregate years by method, e.g. max"""
    df =  df.groupby([df.index.month, df.index.day, df.index.hour]).agg(
        { col: [method] for col in df.columns}
    )
    df.index = df.index.map( lambda m: dt(2016, m[0], m[1], m[2]))  # 2016, beacause this is a leap year
    df.columns = df.columns.droplevel(1)
    return df

def filter_wet_days(dict_of_dfs: dict, num_days: int, treshold: float, lag: int):
    """
    Removes datapoints that is considered to be from "rainy" days.
    What is determined as a rainy day, depends on num_days and value.
    
    Args
        dict_of_dfs: result from reader.get_data, i.e. dfs containing data from all
        stations
        num_days: # of preceding days to concider when summing precipitation
        values including current day
        treshold: max treshold value for the summed precipitation level
    """
    df = dict_of_dfs['vaerdata']
    current_values = [0] * (num_days * 24) # to store precipitation vals
    
    def check_and_update(value):
        # FIFO - keeps length the same
        current_values.pop(0)
        current_values.append(value)
        # In case lag is 0 -> must use len
        return sum(current_values[:len(current_values) - lag]) < treshold
    
    filtered = df[ df['precipitation (mm)'].apply(check_and_update) ]  # filter
    
    return {
        station: (pd.merge(df, filtered, left_index= True, right_index= True)[[
            col for col in df.columns
        ]]
        if station != 'vaerdata' else filtered)
        for station, df in dict_of_dfs.items()
    }