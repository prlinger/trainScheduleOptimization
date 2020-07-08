#!/usr/bin/env python3.7

# Copyright 2020, Gurobi Optimization, LLC

# Found here: file:///Library/gurobi902/mac64/docs/quickstart/py_example_matrix1_py.html

# This example formulates and solves the following simple MIP model
# using the matrix API:
#  maximize
#        x +   y + 2 z
#  subject to
#        x + 2 y + 3 z <= 4
#        x +   y       >= 1
#        x, y, z binary

import numpy as np
import scipy.sparse as sp
import gurobipy as gp
from gurobipy import GRB

test = False



# Initialize data: ------------------------------------------------
# Fixed costs:
loco_Cfix = np.array([(1000,),])
car_Cfix = np.array([100])
# Variable costs (per km):
loco_Ckm = np.array([2])
car_Ckm = np.array([1])
# Train info:
avg_speed = [30]
# Route info:
route_dist = np.array([60])
# Route timings for locos:
period = 60  # This is T in the paper. e.g. trains arrive every 60min.
route_time = 60*np.divide(route_dist, avg_speed)  # time it takes train t to complete route r.  Multply by 60 to convert from hours to minutes
route_num_trains = np.divide(route_time, period)  # This is ceil(t_hat / T)

num_routes = len(route_dist)
num_train_types = len(loco_Cfix)
# End of Initialize data: ------------------------------------------------

# TESTING:
if test:
    x = np.array([1])  # my test values
    w = np.array([4])  # my test values

    fixed_costs = x*np.transpose(loco_Cfix) + w*np.transpose(car_Cfix)
    # variable_costs = np.multiply(route_dist, x*np.transpose(loco_Ckm) + w*np.transpose(car_Ckm))  # multiply element wise by route_distvariable_costs = np.multiply(route_dist, x*np.transpose(loco_Ckm) + w*np.transpose(car_Ckm))  # multiply element wise by route_dist
    variable_costs = route_dist * (x*np.transpose(loco_Ckm) + w*np.transpose(car_Ckm))  # multiply element wise by route_distvariable_costs = np.multiply(route_dist, x*np.transpose(loco_Ckm) + w*np.transpose(car_Ckm))  # multiply element wise by route_dist
    # Calculate number of trains that will be used on each route.
    # This depends on the train choices for each route.
    num_routes = len(route_dist)
    num_trains_per_route = np.multiply(np.identity(num_routes), x*np.transpose(route_num_trains))

    obj = num_trains_per_route * (fixed_costs + variable_costs)
    print(num_trains_per_route)
    print(fixed_costs)
    print(variable_costs)
    print(obj)
    exit(0)

# Initialize Model, Variables, and Objective: ------------------------------------------------

# Create a new model
m = gp.Model("toy_example_v2")

# Add the binary variables x_(r,t) representing if train type t is used on route r
x = m.addMVar(shape=(num_routes, num_train_types), vtype=GRB.BINARY, name="x")

# Add the integer variables w_(r,t) representing the number of coaches of type t on route r
w = m.addMVar(shape=(num_routes, num_train_types), vtype=GRB.INTEGER, name="w")

# Initialize objective:
print(x)
print(loco_Cfix)
print(loco_Cfix.shape)
fixed_costs = x @ np.transpose(loco_Cfix) # + w @ np.transpose(car_Cfix)
variable_costs = route_dist * (x @ np.transpose(loco_Ckm) + w @ np.transpose(car_Ckm))  # multiply element wise by route_dist
num_routes = len(route_dist)  # Calculate number of trains that will be used on each route (depends on train choice for each route)
num_trains_per_route = np.identity(num_routes) * (x @ np.transpose(route_num_trains))

objective = (num_trains_per_route * (fixed_costs + variable_costs)).sum()

m.setObjective(objective, GRB.MINIMIZE)







# Create variables
# x = m.addMVar(shape=3, vtype=GRB.BINARY, name="x")

# Set objective
# obj = np.array([1.0, 1.0, 2.0])
# m.setObjective(obj @ x, GRB.MAXIMIZE)

# Build (sparse) constraint matrix
# data = np.array([1.0, 2.0, 3.0, -1.0, -1.0])
# row = np.array([0, 0, 0, 1, 1])
# col = np.array([0, 1, 2, 0, 1])
#
# A = sp.csr_matrix((data, (row, col)), shape=(2, 3))

# Build rhs vector
# rhs = np.array([4.0, -1.0])

# Add constraints
# m.addConstr(A @ x <= rhs, name="c")

# Optimize model
# m.optimize()
#
# print(x.X)
# print('Obj: %g' % m.objVal)




# except gp.GurobiError as e:
#     print('Error code ' + str(e.errno) + ": " + str(e))
#
# except AttributeError:
#     print('Encountered an attribute error')
