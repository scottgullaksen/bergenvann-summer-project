import pandas as pd
from project.modeling import util
from project.modeling.model_build_scripts import fcnn

# NOT IN USE
def get_predictions(datapoints: list, stations: list) -> dict:
    
    # For each of the stations, get their respective models
    # and create a dataframe of predictions
    return {
        s: util.create_pred_dataframe(
            datapoints, s, util.load(fcnn.build_fcnn, filename=s)
        ) for s in stations if util.model_exists(s)
    }
    
def add_predictions(datapoints, stations: list):
    """
    Adds predictions to the datapoints from the stations
    models if they exist.
    
    Note: The datapoints must be sorted by date for
    this function to work.
    """
    
    station_preds = {}
    
    # Create datastructure to hold stations predictions
    for s in stations:
        
        if not util.model_exists(s):
            print(f'model for {s} do not exist.')
            continue
        
        # Get model, dataset and predictions
        model = util.load(fcnn.build_fcnn, name= s)
        dataset = list(filter(lambda x: s in x, datapoints))
        preds = model.predict(dataset)
        
        # Create datastructure to keep track of 'next' prediction
        date_pred_gen = ((x['date'], y) for x, y in zip(dataset, preds))
        station_preds[s] = {'gen': date_pred_gen, 'next': next(date_pred_gen)}
        
    for dp in datapoints:
        
        # Add pred to stations values in datapoint if correct date
        for s, preds in station_preds.items():
            if preds['next'][0] == dp['date']:
                dp[s]['estimated'] = preds['next'][1]
                try: preds['next'] = next(preds['gen'])
                # End of iterator -> signal stop adding predictions
                except StopIteration: preds['next'] = (None, None)
        
        yield dp


# Check if add datapoints works fine
if __name__ == "__main__":
    from project.data import reader
    
    datapoints = sorted(
        reader().get_data(years= ['2017'], how= 'stream'),
        key= lambda x: x['date']
    )
    
    print(type(datapoints))
    
    stations = ['Gronneviksoren']
    
    for i, dp in enumerate(add_predictions(datapoints, stations)):
        if i == 10: break
        print(i)
        print(dp)
        print()
        