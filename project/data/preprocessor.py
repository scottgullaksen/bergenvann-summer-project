import logging
import os
from datetime import datetime
import pickle
from util import *
from raw_reader import *

# Initialize processing steps for files to be read
PROCESSORS = {
    ps: {'reader': pump_reader, 'cleaner': pump_cleaner} for ps in PUMPSTATIONS
}
PROCESSORS['florida_sentrum'] = {'reader': weather_reader, 'cleaner': florida_cleaner}
PROCESSORS['florida_uib'] = {'reader': weather_reader, 'cleaner': florida_uib_cleaner}
PROCESSORS['tidevannsdata'] = {'reader': tide_reader, 'cleaner': tide_cleaner}
PROCESSORS['snodybde'] = {'reader': weather_reader, 'cleaner': snowdepth_cleaner}

class Preprocessor(object):
    """
    Wrapper for raw reader class. Preprocceses the files/datapoints, 
    and creates and places into organised file structure. This is a convinient
    place to place heavy time/memory consuming preprocessing functions to
    the data such as aggregation, frequency analysis, etc. 

    Args:
        reader (object): The reader object to be wrapped. Provides reading capabilities to the dataset

        target_dir: path to directory where preprocessed files will be placed. If not
        specified it will create one in the same dir as this module.
    """
    def __init__(self, reader: CSVFileReader, target_dir: os.path= None, processors= PROCESSORS):

        self.logger = logging.getLogger('dev')
        self.logger.setLevel(logging.INFO)

        self.reader = reader

        self.target = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'pickled_data'
        ) if not target_dir else target_dir
        
        self.processors = processors

    def save(self, target, data):
        with open(target, 'wb') as f:
            pickle.dump(data, f, pickle.DEFAULT_PROTOCOL)

    def load(self, target):
        parent = os.path.dirname(target)
        if not os.path.exists(parent): os.makedirs(parent)

        if not os.path.exists(target): # File not created yet
            return { 'hours': { } } # Create datastructure 

        with open(target, 'rb') as f:
            return pickle.load(f)

    def transform(self):
        """
        Places all datapoints read from reader into files given by the path:
        target_dir/[year]/[month]/[day].pickle

        The file is pickled dictionary with pickle_keys as keys

        Args:
            pickle_keys: Must be a filename or directory on the path to the
            raw dataset. Distributes the datapoints under that directory/file in the 
            corresponding pickled date dictionary stored under the pickle key.
        """
        last_datapoint = None
        # These correspond to files or directories
        # Their values are descriptions of how to process the respective files under kwrd
        for kwrd in self.processors.keys():
            for datapoint in self.reader.read_datapoints_from(
                self.processors[kwrd]['reader'],
                self.processors[kwrd]['cleaner'],
                dir_or_filename= kwrd
            ):

                # Open a new file if first time through loop or new day
                if not last_datapoint or last_datapoint['date'].date() != datapoint['date'].date():

                    # Save modified datastructure if not first time trough loop
                    if last_datapoint != None: self.save(target, data)

                    target = abspath(self.target, datapoint['date'])
 
                    data = self.load(target)

                for k in datapoint.keys():
                    data['hours'].setdefault(kwrd, {}).setdefault(k, []).append(datapoint[k])
                
                last_datapoint = datapoint     

        self.save(target, data)

# Run to create pickled, preprocessed data folder
if __name__ == "__main__":

    csv_reader = CSVFileReader()

    preprocessor = Preprocessor(reader=csv_reader)

    preprocessor.transform()