#!/usr/bin/env python3.7

# Copyright 2020, Gurobi Optimization, LLC

# Toy example 2 - 3 routes, two train types.

import gurobipy as gp
from gurobipy import GRB



debug = False

try:

    # Create a new model
    m = gp.Model("toy_exampleV5")

    #### Initialize Data: ####

    '''
    ---- Init data for locomotives ----
    loco_types: The type of locomotive.  Corresponds to a train type
    loco_Cfix: Fixed cost of a loco. i.e. cost to purchase one loco
    loco_Ckm: Cost of loco travelling 1km
    loco_speed: Average speed of locomotive

    e.g. locomotive 'a' costs 1000 to purchase and 2 per km to run, avg speed of 30km/h
    '''
    loco_types, loco_Cfix, loco_Ckm, loco_speed = gp.multidict({ 'a': [1000, 2, 40],
                                                                 'b': [2000, 4, 80] })
    if debug:
        print("loco_types, loco_Cfix, loco_Ckm, loco_speed:")
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
    car_types, car_Cfix, car_Ckm, car_cap, car_min, car_max = gp.multidict({ 'a': [100, 1, 10, 1, 8],
                                                                             'b': [200, 2, 10, 1, 4] })
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
    stations = ['s1', 's2', 's3']
    edges, edge_len, edge_Npassengers = gp.multidict({
                                                        ('s1','s2'): [40,40],
                                                        ('s2','s3'): [80,20] })
    routes, route_edges, route_dist = gp.multidict({
                                                    'r1': [[('s1','s2')], 80],
                                                    'r2': [[('s2','s3')], 160]})


    # TODO: initialize route_dist by looping through edges.
    if debug:
        print("routes, route_edges, route_dist")
        print(routes)
        print(route_edges)
        print(route_dist)

    # Init period (variable T in the paper):
    # TODO: let each route have a different period
    period = 60  # The period is an hour

    '''
    Init cycle time by train type on each route.  The dict key is the route and train type.
    e.g. route ('s1','s2','s1') for train 'a' takes 120 minutes
    '''
    # TODO: Calculate in loop from loco_speed and route_dist
    cycle_times = { 'r1': {'a': 120, 'b': 60},
                    'r2': {'a': 240, 'b': 120} }

    '''
    Init number of trains:
    e.g. route ('s1','s2','s1') would require 2 trains of type 'a'
    '''
    # TODO: calculate from cycle times and period.
    num_trains = { 'r1': {'a': 2, 'b': 1},
                   'r2': {'a': 4, 'b': 2} }


    # Create Variables and Set Objective: ------------------------------------------------------------------------------

    # Create and add the binary variables x_(r,t) representing if train type t is used on route r
    x_rt = m.addVars(routes, loco_types, vtype=GRB.BINARY, name="x_rt")  # returns a tuple dict.  e.g. x_rt['r1', 'a']

    # Create and add the integer variables w_(r,t) representing the number of coaches of type t on route r
    w_rt = m.addVars(routes, loco_types, vtype=GRB.INTEGER, name="w_rt")

    # Set objective
    obj = 0
    for route in routes:
        for loco_type in loco_types:
            fixed_costs = x_rt[route, loco_type]*loco_Cfix[loco_type] + w_rt[route, loco_type]*car_Cfix[loco_type]
            variable_costs = route_dist[route] * (x_rt[route, loco_type]*loco_Ckm[loco_type] + w_rt[route, loco_type]*car_Ckm[loco_type])
            obj += num_trains[route][loco_type] * (fixed_costs + variable_costs)

    # Set objective
    m.setObjective(obj, GRB.MINIMIZE)


    # Add Constraints: -------------------------------------------------------------------------------------------------

    # Add constraints on decision variables:
    for route in routes:
        for loco_type in loco_types:
            # Min/Max allowed number of cars
            m.addConstr(w_rt[route, loco_type] >= car_min[loco_type]*x_rt[route, loco_type], "car_min_rt_{}_{}".format(route, loco_type))
            m.addConstr(w_rt[route, loco_type] <= car_max[loco_type] * x_rt[route, loco_type], "car_min_rt_{}_{}".format(route, loco_type))


    # Add constraints based on properties rail network. (e.g. passenger capacity).
    for route in routes:
        cur_route_capacity = sum((w_rt[route, loco_type] * car_cap[loco_type]) for loco_type in loco_types)
        for edge in route_edges[route]:
            # Add constraint that the passenger requirements for each edge are met.
            m.addConstr(edge_Npassengers[edge] <= cur_route_capacity)


    # Optimize and Print Results: --------------------------------------------------------------------------------------

    # Optimize model
    m.optimize()

    for v in m.getVars():
        print('%s %g' % (v.varName, v.x))

    print('Obj: %g' % m.objVal)

except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')
