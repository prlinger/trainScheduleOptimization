# trainScheduleOptimization

The models can be run as a single python script.
The main models are:
- level1/level1_model.py
- level2/level2_model.py
- level3/level3_model.py

Gurobi must be installed on your environment.
There are a variety of ways to do this.  Please refer to the documentation at gurobi.com for Python on you respective system.

The script can be run from the command line like so:
gurobi.sh level3/level3_model.py

It can also be run as a Python script if you have Gurobi installed in your environment.
I created a virtualenv with Gurobi installed.

Each folder contains the model with real-world data, the model with toy data, and their respective outputs saved in a file from when I ran the models.
Note, the code for each model is the same, I just copied it and change the data so that the scripts can be run individually without making any code changes.






