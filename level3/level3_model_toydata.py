#!/usr/bin/env python3.7

# Copyright 2020, Gurobi Optimization, LLC

# Level 3 model:
# - PESP constraints include station wait time and padding.
# - PESP constraint for overlap of routes at Union station.
# - Two routes
# - Two locomotive types

import gurobipy as gp
from gurobipy import GRB
import numpy as np
from math import ceil

# This is required to allow for multiple train type.  If the default value (-1) is used, we get error:
# Error code 10020: Objective Q not PSD (diagonal adjustment of 2.3e+02 would be required). Set NonConvex parameter to 2 to solve model.
gp.setParam("NonConvex", 2)

debug = False
# debug = True

try:

    # Create a new model
    m = gp.Model("level3_toydata")

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
    loco_types, loco_Cfix, loco_Ckm, loco_speed = gp.multidict({'a': [1000, 2, 40],
                                                                'b': [2000, 4, 80]})
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
    car_types, car_Cfix, car_Ckm, car_cap, car_min, car_max = gp.multidict({'a': [100, 1, 10, 1, 8],
                                                                            'b': [200, 2, 10, 1, 4]})
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
    e.g. edge (s1,s2) is 30km long and must trans    e.g. edge (s1,s2) is 30km long and must transport 40 passengers (and the reverse)
port 40 passengers (and the reverse)
         The route is (s1,s2,s1) and is 60km long.  Note, all routes are cycles.
    
    Note:  Since ridership is greatest between the stations Union and York University, the edge capacity
            is fixed by this maximum capacity. 
    '''
    stations = {'r1': ['s1', 's2'], 'r2': ['s2', 's3']}
    edge_len = { 'r1': {('s1', 's2'): 40}, 'r2': {('s2', 's3'): 80} }
    edge_Npassengers = { 'r1': {('s1', 's2'): 40}, 'r2': {('s2', 's3'): 20} }
    routes, route_edges, route_dist = gp.multidict({
        'r1': [[('s1', 's2')], 80],
        'r2': [[('s2', 's3')], 160]})
    route_to_name = {'r1': "Route1", 'r2': "Route2"}
    station_to_name = {'r1': {'s1': "Station1", 's2': "Station2"},
                       'r2': {'s2': "Station2", 's3': "Station3"}}

    if debug:
        print("routes, route_edges, route_dist")
        print(routes)
        print(route_edges)
        print(route_dist)

    # Init period (variable T in the paper):
    period = 60  # The period is an hour


    # Create Variables and Set Objective: ------------------------------------------------------------------------------

    # Create and add the binary variables x_(r,t) representing if train type t is used on route r
    x_rt = m.addVars(routes, loco_types, vtype=GRB.BINARY, name="x_rt")  # returns a tuple dict.  e.g. x_rt['r1', 'a']

    # Create and add the integer variables w_(r,t) representing the number of coaches of type t on route r
    w_rt = m.addVars(routes, loco_types, vtype=GRB.INTEGER, name="w_rt")

    # Additions for Level 2:
    # - The estimated cycle time is now a decision variable (this is used in the objective to determine the number of trains used)
    # - PESP constraints are added along with arrival/departure times.

    # Initialize arrival/departure time variables:
    # The arrival time at station v on route r with direction u.
    # The direction is 0 if going in order increasing stations.  e.g. ('s1', 's2').
    # It is zero if decreasing. e.g. ('s2', 's1').
    # The structure is as follows: arrival_times[route][direction][edge]
    arrival_times = {}
    departure_times = {}
    for route in routes:
        route_arrival_times = { 0: {}, 1: {} }
        route_departure_times = { 0: {}, 1: {} }
        for edge in route_edges[route]:
            # Do forward direction (increasing station numbers)
            dep_forward  = m.addVar(vtype=GRB.CONTINUOUS, name="d_{}_{}_{}".format(route, edge[0], 0))  # This is departing from s_i-1 to s_i.
            arr_forward = m.addVar(vtype=GRB.CONTINUOUS, name="a_{}_{}_{}".format(route, edge[1], 0))  # This is arriving to s_i from s_i-1
            route_departure_times[0][edge] = dep_forward
            route_arrival_times[0][edge] = arr_forward
            # Do reverse direction (decreasing station numbers)
            dep_reverse = m.addVar(vtype=GRB.CONTINUOUS, name="d_{}_{}_{}".format(route, edge[1], 1))  # This is departing from s_i to s_i-1.
            arr_reverse = m.addVar(vtype=GRB.CONTINUOUS, name="a_{}_{}_{}".format(route, edge[0], 1))  # This is arriving to s_i-1 from s_i
            route_departure_times[1][edge] = dep_reverse
            route_arrival_times[1][edge] = arr_reverse
        arrival_times[route] = route_arrival_times
        departure_times[route] = route_departure_times

    if debug:
        print("Arrival Times: - - - -")
        print(arrival_times)
        print("Departure Times: - - - -")
        print(departure_times)

    # Initialize estimated cycle time for train type t on route r.  This it t_hat in the paper.
    # The structure is: cycle_times[route][loco_type]
    cycle_times = {}
    for route in routes:
        route_cycle_times = {}
        for loco_type in loco_types:
            route_cycle_times[loco_type] = m.addVar(vtype=GRB.CONTINUOUS, name="cycletime_{}_{}".format(route, loco_type))
        cycle_times[route] = route_cycle_times

    # Set objective (level2/3 is quadratic instead of linear)
    obj = 0
    for route in routes:
        for loco_type in loco_types:
            fixed_costs = x_rt[route, loco_type]*loco_Cfix[loco_type] + w_rt[route, loco_type]*car_Cfix[loco_type]
            variable_costs = route_dist[route] * (x_rt[route, loco_type]*loco_Ckm[loco_type] + w_rt[route, loco_type]*car_Ckm[loco_type])
            # obj += level1_num_trains[route][loco_type] * (fixed_costs + variable_costs)  # Level 1
            obj += (cycle_times[route][loco_type] / period) * (fixed_costs + variable_costs)

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
            m.addConstr(edge_Npassengers[route][edge] <= cur_route_capacity)

    # Add Level 2 and some level 3 Constraints:

    # Constraint to ensure the train does not exceed its max speed between any pair of stations.
    # the LHS is speed on edge and the RHS is the max speed of train.
    # - if the loco type is not used on the route, LHS == RHS == 0.
    for route in routes:
        for loco_type in loco_types:
            for edge in route_edges[route]:
                # Forward direction (going from s_i-1 to s_i).
                # The structure is: arrival_times[route][direction][edge]
                # We have distance / (arrival at s_i - departure at s_i-1).  i.e. distance/time = velocity
                # fwd_speed = edge_len[edge] / (arrival_times[route][0][edge] - departure_times[route][0][edge])  # Error code 10003: Divisor must be a constant
                # m.addConstr(x_rt[route, loco_type] * fwd_speed <= x_rt * loco_speed[loco_type])
                # The following fixes the error and is equivalent since arrival_times[route][0][edge] >= departure_times[route][0][edge]
                m.addConstr(x_rt[route, loco_type] * edge_len[route][edge]
                            <=
                            x_rt[route, loco_type] * loco_speed[loco_type] * (arrival_times[route][0][edge] - departure_times[route][0][edge]))
                # The reverse direction:
                m.addConstr(x_rt[route, loco_type] * edge_len[route][edge]
                            <=
                            x_rt[route, loco_type] * loco_speed[loco_type] * (arrival_times[route][1][edge] - departure_times[route][1][edge]))

    # Constraints to ensure that stations are visited in order:
    # Also to ensure that each station is waited at for at least 1 minute.
    # Note: Waiting at a station also creates padding/headway between trains since they all follow
    #   the same cyclic schedule.
    wait_time_at_station = 1
    for route in routes:
        i = 0
        route_len = len(route_edges[route])
        # Forward direction:
        # - Departing from edge[0] to edge[1].  e.g. s3 to s4 in edge ('s3', 's4')
        while i < route_len:
            edge = route_edges[route][i]
            if i != 0: # and i != route_len-1:
                prev_edge = route_edges[route][i - 1]
                # Ensure station departing from has been arrived at in previous edge.
                m.addConstr(departure_times[route][0][edge] >= arrival_times[route][0][prev_edge] + (wait_time_at_station / period))
            # Ensure we arrive at the next station in edge after we depart.
            m.addConstr(arrival_times[route][0][edge] >= departure_times[route][0][edge])
            i += 1

        # Constraint for the turn-around point on each route:
        # The loco departs the last station on direction 1 (reverse) after it arrives in direction 0 (forward).
        turnaround = route_edges[route][-1]  # The last edge.
        m.addConstr(departure_times[route][1][turnaround] >= arrival_times[route][0][turnaround] + (wait_time_at_station / period))

        # Reverse direction:
        i = route_len - 1
        while i >= 0:
            edge = route_edges[route][i]
            if i != route_len - 1: # and i != route_len-1:
                prev_edge = route_edges[route][i + 1]
                # Ensure station departing from has been arrived at in previous edge.
                m.addConstr(departure_times[route][1][edge] >= arrival_times[route][1][prev_edge] + (wait_time_at_station / period))
            # Ensure we arrive at the next station in edge after we depart.
            m.addConstr(arrival_times[route][1][edge] >= departure_times[route][1][edge])
            i -= 1

    # Constraint to set the value of the cycle time of route r for locomotive of type t
    # The total cycle time is equal to the arrival time back at station 1 on the route.
    # Note: cycle time is set to zero if loco type is not used on route.
    for route in routes:
        for loco_type in loco_types:
            # The structure is: cycle_times[route][loco_type]
            first_station = route_edges[route][0]
            m.addConstr(x_rt[route, loco_type] * cycle_times[route][loco_type]
                        ==
                        x_rt[route, loco_type] * arrival_times[route][1][first_station])


    # More Level 3 constraints:
    # Ensure trains overlap at union station for at least 5 minutes:
    union_overlap_time = (5 / period)
    union_r1 = route_edges['r1'][0]
    union_r2 = route_edges['r2'][0]
    m.addConstr(departure_times['r1'][0][union_r1] >= union_overlap_time)
    m.addConstr(departure_times['r2'][0][union_r2] >= union_overlap_time)



    # Optimize and Print Results: --------------------------------------------------------------------------------------

    # Optimize model
    m.optimize()


    def value_to_minutes(val):
        return val*60

    print("\nStation to name mapping: - - - -")
    for route in routes:
        print("\tRoute {} == {}:".format(route, route_to_name[route]))
        for station in stations[route]:
            print("\t\t{} -> {}".format(station, station_to_name[route][station]))

    print("\nLocomotive and Coach values for each route: - - - -")
    print("\tNote: x_rt is binary.  1 if type t is used on route r.  Similar, w_rt is the number of coaches for type t")
    for route in routes:
        print("\tRoute {}:".format(route))
        for loco_type in loco_types:
            print("\t\tNumber of loco used: {}".format(ceil(cycle_times[route][loco_type].x * 60 / period)))
            print("\t\t{} {}".format(x_rt[route, loco_type].varName, x_rt[route, loco_type].x))
            print("\t\t{} {}".format(w_rt[route, loco_type].varName, w_rt[route, loco_type].x))


    print("\nRoute Schedules: - - - -")
    for route in routes:
        print("\n\tRoute {} - formatted (station event, event time in units of period, event time in minutes):".format(route))
        for edge in route_edges[route]:
            depart_var = departure_times[route][0][edge]
            arrive_var = arrival_times[route][0][edge]
            print("\t\t{} {} {}m".format(depart_var.varName, depart_var.x, value_to_minutes(depart_var.x)))
            print("\t\t{} {} {}m".format(arrive_var.varName, arrive_var.x, value_to_minutes(arrive_var.x)))
        print("\t\t - - Turn around point - -")
        for edge in reversed(route_edges[route]):
            depart_var = departure_times[route][1][edge]
            arrive_var = arrival_times[route][1][edge]
            print("\t\t{} {} {}m".format(depart_var.varName, depart_var.x, value_to_minutes(depart_var.x)))
            print("\t\t{} {} {}m".format(arrive_var.varName, arrive_var.x, value_to_minutes(arrive_var.x)))

    print("\nCycle Times: - - - -")
    for route in routes:
        print("\tRoute {}:".format(route))
        for loco_type in loco_types:
            print("\t\t{} {} {}m".format(cycle_times[route][loco_type].varName,
                                        cycle_times[route][loco_type].x, value_to_minutes(cycle_times[route][loco_type].x)))

    print("\n########\nThe Objective Value is {}\n########".format(m.objVal))

except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ': ' + str(e))

except AttributeError:
    print('Encountered an attribute error')
