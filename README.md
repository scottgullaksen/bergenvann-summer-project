# Bergen Vann Summer Project

Bergen vann has available, but currently unused, data from sensors equpped in their drain pipes and -pumps. The intuition is that this data should be helpful for detecting, and perhaps even anticipating, unwanted events such as pipe leaks or pump shutdowns. However, as of now this data is neither presented or made available in a way that makes such analyses possible. The aim of this project is to enable visualization of the data to
1. Showcase that anamoly detection is indeed possible
2. Help Bergen Vann understand their data better
3. See value in their unused data

There's also some correlated metereology data which should help for predictive purposes.

# Setup (for further development)

## Requirements
The follwing must be installed on your local machine.
- Python, or python virtual environment manager, like e.g Anaconda
- pip python package manager

Recommended
- Python virtual environment manager. Conda venv was mostly used. 
- Your favorite IDE, e.g. VS code

## Steps
After cloning/forking the repo to your local machine, on your machines CLI,
change your current working directory to the root git repo.
Then simply do the pip command
'
pip install -r requirements.txt
'
This will download and install all necessary dependencies so
you can continue with development

# Running the app on localhost
After following all of the above steps, simply run
the app.py file under the folder "project".

# Heroku
There is deployed version running on Heroku's server at
https://bergenvann-pumpedata.herokuapp.com/

Note however that there is a memory problem on this server
where the RAM limit is reached after some usage. This is because
of the tensorflow package which is extremely large.
In the future it is recomended that this module is only used when data
is fetched from server and then comupte new estimations which could be pickled
as well. Currently the module is used every time the user checks "estimat"
checkbox in the UI.

# Other
## tensorflow gpu
The requirements.txt file specifies the cpu version of tensorflow.
If you would like to make use of the gpu version simply do:
- pip install tensorflow
in the CLI