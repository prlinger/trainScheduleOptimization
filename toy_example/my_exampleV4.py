#!/usr/bin/env python3.7

'''
This is the toy example for Adam and Paul's CO454 project.
This same toy example is also typed out in our revised outline.
'''

import gurobipy as gp
from gurobipy import GRB, quicksum
import numpy as np

debug = True

try:

    # Create a new model
    m = gp.Model("toy_exampleV4")

    #### Initialize Data: ####

    # Init data for locomotives
    train_types = ['a']  # This is the type for both locomotive and cars

    '''
    ---- Init data for locomotives ----
    loco_types: The type of locomotive.  Corresponds to a train type
    loco_Cfix: Fixed cost of a loco. i.e. cost to purchase one loco
    loco_Ckm: Cost of loco travelling 1km
    loco_speed: Average speed of locomotive
    
    e.g. locomotive 'a' costs 1000 to purchase and 2 per km to run, avg speed of 30km/h
    '''
    loco_type = 'a'
    loco_Cfix = 1000
    loco_Ckm = 2
    loco_speed = 30

    '''
    ---- Init data for coaches/cars: ----
    car_types: The car type. Corresponds to a train type
    car_Cfix: Fixed cost of a car. i.e. cost to purchase one car
    car_Ckm: Cost of car travelling 1km
    car_cap: Capacity of car.  i.e. number of passengers it can fit
    car_min: Minimum number of this car type allowed on a train
    car_max: Maximum number of this car type allowed on a train
    
    e.g. car of type 'a' costs 100 to buy, 1 per km to run, and has capacity of 10 passengers
    '''
    car_type = 'a'
    car_Cfix = 100
    car_Ckm = 1
    car_cap = 10
    car_min = 1
    car_max = 8

    '''
    Init data for routes and stations:
    e.g. edge (s1,s2) is 30km long and must transport 40 passengers (and the reverse)
         The route is (s1,s2,s1) and is 60km long.  Note, all routes are cycles.
    '''
    stations = ['s1', 's2']
    edge = ('s1', 's2')
    edge_len = 20
    edge_Npassenger = 40

    route = 'r1'
    route_edges = ('s1','s2','s1')
    route_dist = 60


    # Init period (variable T in the paper):
    # TODO: let each route have a different period
    period = 60  # The period is an hour

    '''
    Init cycle time by train type on each route.  The dict key is the route and train type.
    e.g. route ('s1','s2','s1') for train 'a' takes 120 minutes
    '''
    # TODO: Calculate in loop from loco_speed and route_dist
    route_cycle_time = 120

    '''
    Init number of trains:
    e.g. route ('s1','s2','s1') would require 2 trains of type 'a'
    '''
    # TODO: calculate from cycle times and period.
    route_num_trains = 2


    # Create Variables: ------------------------------------------------------

    # Add the binary variables x_(r,t) representing if train type t is used on route r
    x_ar1 = m.addVar(vtype=GRB.BINARY, name="x_ar1")

    # Add the integer variables w_(r,t) representing the number of coaches of type t on route r
    w_ar1 = m.addVar(vtype=GRB.INTEGER, name="w_ar1")

    objective = route_num_trains * ((x_ar1*loco_Cfix + w_ar1*car_Cfix) + route_dist*(x_ar1*loco_Ckm + w_ar1*car_Ckm))
    m.setObjective(objective, GRB.MINIMIZE)


    # Add constraints on decision variables:
    m.addConstr(w_ar1 >= car_min * x_ar1, "c0_cars")
    m.addConstr(w_ar1 <= car_max * x_ar1, "c1_cars")
    m.addConstr(x_ar1 == 1)

    # Add constraints for passenger carrying:
    m.addConstr(car_cap*w_ar1 >= edge_Npassenger)


    # Optimize model
    m.optimize()

    for v in m.getVars():
        print('%s %g' % (v.varName, v.x))

    print('Obj: %g' % m.objVal)

except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')
