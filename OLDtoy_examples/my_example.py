#!/usr/bin/env python3.7

# Copyright 2020, Gurobi Optimization, LLC

# This example formulates and solves the following simple MIP model:
#  maximize
#        x +   y + 2 z
#  subject to
#        x + 2 y + 3 z <= 4
#        x +   y       >= 1
#        x, y, z binary

import gurobipy as gp
from gurobipy import GRB
import numpy as np

debug = True

try:

    # Create a new model
    m = gp.Model("toy_example")

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
    loco_types, loco_Cfix, loco_Ckm, loco_speed = gp.multidict({ 'a': [1000, 2, 30] })
    if debug:
        print("loco_names, loco_Cfix, loco_Ckm, loco_speed:")
        print(loco_types)
        print(loco_Cfix)
        print(loco_Ckm)
        print(loco_speed)

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
    car_types, car_Cfix, car_Ckm, car_cap, car_min, car_max = gp.multidict({ 'a': [100, 1, 10, 1, 8] })
    if debug:
        print("\ncar_types, car_Cfix, car_Ckm, car_cap, car_min, car_max:")
        print(car_types)
        print(car_Cfix)
        print(car_Ckm)
        print(car_cap)
        print(car_min)
        print(car_max)

    '''
    Init data for routes and stations:
    e.g. edge (s1,s2) is 30km long and must transport 40 passengers (and the reverse)
         The route is (s1,s2,s1) and is 60km long.  Note, all routes are cycles.
    '''
    stations = ['s1', 's2']
    edges, edge_len, edge_Npassengers = gp.multidict({
                                                      ('s1','s2'): [30,40],
                                                      ('s2','s1'): [30,40] })
    routes, route_dist = gp.multidict({ ('s1','s2','s1'): [60] })
    # TODO: initialize route_dist by looping through edges.

    # Init period (variable T in the paper):
    # TODO: let each route have a different period
    period = 60  # The period is an hour

    '''
    Init cycle time by train type on each route.  The dict key is the route and train type.
    e.g. route ('s1','s2','s1') for train 'a' takes 120 minutes
    '''
    # TODO: Calculate in loop from loco_speed and route_dist
    cycle_times = { ('s1','s2','s1'): {'a': 120} }

    '''
    Init number of trains:
    e.g. route ('s1','s2','s1') would require 2 trains of type 'a'
    '''
    # TODO: calculate from cycle times and period.
    num_trains = { (('s1','s2','s1'), 'a'): 2 }



    # Create variables
    # x = m.addVar(vtype=GRB.BINARY, name="x")
    # y = m.addVar(vtype=GRB.BINARY, name="y")
    # z = m.addVar(vtype=GRB.BINARY, name="z")







    # Set objective
    # m.setObjective(x + y + 2 * z, GRB.MAXIMIZE)

    # Add constraint: x + 2 y + 3 z <= 4
    # m.addConstr(x + 2 * y + 3 * z <= 4, "c0")

    # Add constraint: x + y >= 1
    # m.addConstr(x + y >= 1, "c1")

    # Optimize model
    # m.optimize()

    # for v in m.getVars():
    #     print('%s %g' % (v.varName, v.x))
    #
    # print('Obj: %g' % m.objVal)

except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')
