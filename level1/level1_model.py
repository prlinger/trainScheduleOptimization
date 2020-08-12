#!/usr/bin/env python3.7

# Copyright 2020, Gurobi Optimization, LLC

# Toy example 2 - 3 routes, two train types.

import gurobipy as gp
from gurobipy import GRB
from math import ceil


# debug = False
debug = True

try:

    # Create a new model
    m = gp.Model("level1")

    #### Initialize Data: ####

    '''
    ---- Init data for locomotives ----
    loco_types: The type of locomotive.  Corresponds to a train type
    loco_Cfix: Fixed cost of a loco. i.e. cost to purchase one loco
    loco_Ckm: Cost of loco travelling 1km
    loco_speed: Average speed of locomotive

    e.g. locomotive 'a' costs 1000 to purchase and 2 per km to run, avg speed of 30km/h
    Note: I have set the fixed cost to zero since the locos are already owned, and this does not affect daily
    operation as much.  The millions of dollars in fixed cost overshadows the cost of operating.
    '''
    loco_types, loco_Cfix, loco_Ckm, loco_speed = gp.multidict({ 'MP40': [0, 98.09, 91] })
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
    car_types, car_Cfix, car_Ckm, car_cap, car_min, car_max = gp.multidict({ 'MP40': [0, 37.26, 162, 1, 12] })
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
    
    Note:  Since ridership is greatest between the stations Union and York University, the edge capacity
            is fixed by this maximum capacity. 
    '''
    stations = ['s1','s2','s3','s4','s5','s6','s7','s8','s9','s10','s11']
    station_to_name = {'s1': "Union", 's2': "York University", 's3': "Rutherford", 's4': "Maple",
                       's5': "King City", 's6': "Aurora", 's7': "Newmarket", 's8': "East Gwillimbury",
                       's9': "Bradford", 's10': "Barrie South", 's11': "Allendale"}
    edges, edge_len, edge_Npassengers = gp.multidict({
                                                        ('s1','s2'): [17.54, 550],
                                                        ('s2','s3'): [9.34, 550],
                                                        ('s3','s4'): [2.57, 550],
                                                        ('s4','s5'): [7.08, 550],
                                                        ('s5','s6'): [11.59, 550],
                                                        ('s6','s7'): [6.93, 550],
                                                        ('s7','s8'): [2.08, 550],
                                                        ('s8', 's9'): [9.66, 550],
                                                        ('s9', 's10'): [28.97, 550],
                                                        ('s10', 's11'): [5.63, 550] })
    [('s1','s2'), ('s2','s3'), ('s3','s4'), ('s4','s5'), ('s5','s6'), ('s6','s7'), ('s7','s8'), ('s8', 's9'), ('s9', 's10'), ('s10', 's11')]
    routes, route_edges, route_dist = gp.multidict({
        'r1': [[('s1','s2'), ('s2','s3'), ('s3','s4'), ('s4','s5'), ('s5','s6'), ('s6','s7'), ('s7','s8'), ('s8', 's9'), ('s9', 's10'), ('s10', 's11')],
               101.39]
    })

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

    def calc_cycle_time(route_key, loco_key):
        return (route_dist[route_key] * 2 / loco_speed[loco_key]) * 60

    cycle_times = { 'r1': { 'MP40': calc_cycle_time('r1', 'MP40') } }

    if debug:
        print("- - - - cycle_times:")
        print(cycle_times)

    '''
    Init number of trains:
    e.g. route ('s1','s2','s1') would require 2 trains of type 'a'
    '''
    # TODO: calculate from cycle times and period.
    def calc_num_trains(route_key, loco_key):
        return ceil( cycle_times[route_key][loco_key] / period )

    num_trains = { 'r1': {'MP40': calc_num_trains('r1', 'MP40') } }

    if debug:
        print("- - - - num_trains:")
        print(num_trains)

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
