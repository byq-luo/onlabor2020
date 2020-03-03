import sys
import os
import traci
from vehicles import *
from Clustering import *
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from collections import Counter
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
traci.start(["sumo-gui", "-c", "test.sumocfg"])

city = Map(traci.edge.getIDList())
# TODO at kell irni


step = 0
while step < 200:
    traci.simulationStep()
    step += 1
    if len(traci.vehicle.getIDList()) > 3:
        print("\n\nNew step:", step)

    # TODO: Stuff here
    # update road database:
    # flush cars no longer on roads:
    city.flush()

    # add vehicles to road:
    for veh_id in traci.vehicle.getIDList():
        this_road = traci.vehicle.getRoadID(veh_id)
        for road in city.roads:
            if road.road_id == this_road:
                road.addcar(Vehicle(veh_id, traci.vehicle.getPosition(veh_id), road.road_id))

    # TODO try printing the cars on the roads: for DBSCAN
    # Get the vehicles and their positions for each road seperatly, and run DBSCAN on it

    arr = []
    for road in city.roads:
        #FIXME ez ugy is lehetne hogy csak egyszer fut le a DBSCAN
        for car in road.cars_on_this_road:
            arr.append([car.vehicle_id, car.road_id, car.position[0], car.position[1]])

    arr = np.array(arr)
    if len(arr) > 2:
        ass = DBSCAN(eps=40, min_samples=2, metric=similarity).fit(arr.astype(np.float64))
        print(ass.labels_)
        runner = 0
        x = ass.labels_

        for road in city.roads:
            for car in road.cars_on_this_road:
                Bass = x[runner]
                if Bass == -1:
                    traci.vehicle.setColor(car.vehicle_id, [255, 255, 255])
                else:
                    traci.vehicle.setColor(car.vehicle_id, [50, 200, 50])
                runner += 1

    # city.print()

traci.close(True)
