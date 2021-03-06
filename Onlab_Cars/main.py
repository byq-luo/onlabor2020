import copy
import sys
import os
import traci
from vehicles import *
from Clustering import *
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.metrics import jaccard_score
from collections import Counter
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt


def jaccard_similarity(list1, list2):
    s1 = set(list1)
    s2 = set(list2)
    return len(s1.intersection(s2)) / len(s1.union(s2))


sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
traci.start(["sumo-gui", "-c", "pecs_belvaros_cut.sumocfg"])
colours = [(230, 25, 75), (60, 180, 75), (255, 225, 25), (0, 130, 200), (245, 130, 48), (145, 30, 180), (70, 240, 240),
           (240, 50, 230), (210, 245, 60), (250, 190, 190), (0, 128, 128), (230, 190, 255), (170, 110, 40),
           (255, 250, 200), (128, 0, 0), (170, 255, 195), (128, 128, 0), (255, 215, 180), (0, 0, 128), (128, 128, 128),
           (255, 255, 255), (255, 255, 255)]

old_clusters = {}
temp_clusters = {}


current_prio = -1



city = Map(traci.edge.getIDList())
# TODO at kell irni

# Basically infinite phase duration
# for tls in traci.trafficlight.getIDList():
#     traci.trafficlight.setPhaseDuration(tls, 12000)

step = 0
while step < 500:
    clusters_life = []
    clusters_edge = []

    for i in range(0, 50):
        clusters_life.append(0)

    for i in range(0, 50):
        clusters_edge.append("")


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
        # FIXME ez ugy is lehetne hogy csak egyszer fut le a DBSCAN
        for car in road.cars_on_this_road:
            arr.append([car.vehicle_id, car.road_id, car.position[0], car.position[1]])

    arr = np.array(arr)
    if len(arr) > 2:
        done_clusters = DBSCAN(eps=40, min_samples=3, metric=similarity).fit(arr.astype(np.float64))

        # print(done_clusters.labels_)
        runner = 0
        x = done_clusters.labels_
        no_ofclusters = max(done_clusters.labels_) + 1

        # TODO valahol itt kene a dictionarybe bele rakni string formaban a nevet keynek meg h melyik clusterben van
        for road in city.roads:
            for car in road.cars_on_this_road:
                key = x[runner]
                if key == -1:
                    traci.vehicle.setColor(car.vehicle_id, colours[21])

                else:
                    # traci.vehicle.setColor(car.vehicle_id, colours[key % 22])
                    temp_clusters.setdefault(key, set()).add(car.vehicle_id)

                runner += 1

        # print("New clustered formed: ", temp_clusters)
        # print("Previous clusters:", old_clusters)
        new_clusters = {}
        old_temp_clusters = {}

        # TODO check similarity here

        for i in temp_clusters:
            overwritten = False

            for j in old_clusters:
                if overwritten == False:
                    # print("Comparing: {} with {}".format(j, i), jaccard_similarity(old_clusters[j], temp_clusters[i]))
                    if jaccard_similarity(old_clusters[j], temp_clusters[i]) >= 0.25:
                        old_temp_clusters[j] = temp_clusters[i]
                        # print("Similar: Old[{}], New[{}]".format(j, i))
                        overwritten = True

            if overwritten == False:
                # egy temp dictionaryba berakja
                # print("Not similar")
                for k in range(0, 100):
                    if k not in new_clusters.keys():
                        new_clusters[k] = temp_clusters[i]

                        break

        if len(old_clusters) == 0:
            # print("No old clusters")
            for i in temp_clusters:
                for k in range(0, 100):
                    if k not in new_clusters.keys():
                        new_clusters[k] = temp_clusters[i]

                        break

        old_clusters = copy.deepcopy(old_temp_clusters)
        # print("\nTotally new clusters: ", new_clusters)
        # print("Old_temp:", old_temp_clusters)

        for k in new_clusters:
            for i in range(1, 100):
                if i not in old_clusters.keys():
                    old_clusters[i] = new_clusters[k]

                    break

        # print("OLD:", old_clusters)

        result = {}

        for key, value in old_clusters.items():
            if value not in result.values():
                result[key] = value

        old_clusters = copy.deepcopy(result)
        print(old_clusters)

        for i in range(0, len(clusters_life)):
            if i in old_clusters.keys():
                # print("this cluster is alive:", i)
                clusters_life[i] += 1
            else:
                # print("this cluster is dead:", i)
                clusters_life[i] = 0

        print("\nClusters Edge:")

        # Finding what edge a cluster is on
        for i in old_clusters:
            print(old_clusters[i])
            for j in old_clusters[i]:
                clusters_edge[i] = traci.vehicle.getRoadID(j)
                break
            print(i, ": ", clusters_edge[i], "with a size of: ", len(old_clusters[i]))

        x = 0
        for i in clusters_life:
            if i != 0:
                pass
                # print(x, ": ", i)
            x += 1

        for i in old_clusters:
            for j in old_clusters[i]:
                traci.vehicle.setColor(j, colours[i % 22])

        # old_clusters = copy.deepcopy(temp_clusters)
        temp_clusters.clear()



    # TODO: Generalization for all TLS on the map:

    # if step % 20 == 0:
    #     print("Testing Traffic Light controls:")
    #     for tls in traci.trafficlight.getIDList():
    #         # traci.trafficlight.setPhaseDuration(tlsID=tls, phaseDuration= 30)
    #         new_state = int(60 / max(step % 100, 20))
    #         print("\n\nID:", tls, "State:", traci.trafficlight.getPhase(tlsID=tls))
    #         print("Complete Def:", traci.trafficlight.getCompleteRedYellowGreenDefinition(tlsID=tls))
    #         print("Get Next Switch:", traci.trafficlight.getNextSwitch(tlsID=tls))
    #
    #         print("Controlled Lanes:", traci.trafficlight.getControlledLanes(tlsID=tls))
    #         print("Controlled Links:", traci.trafficlight.getControlledLinks(tlsID=tls))
    #
    #         # traci.trafficlight.setPhase(tlsID=tls, index=new_state)
    #         # print("\n\n\nTraffic Light state changed:", new_state)

    tls = "South_East_TL"
    print("\n\nID:", tls, "State:", traci.trafficlight.getPhase(tlsID=tls))
    print("Complete Def:", traci.trafficlight.getCompleteRedYellowGreenDefinition(tlsID=tls))
    print("Get Next Switch:", traci.trafficlight.getNextSwitch(tlsID=tls))

    print("Controlled Lanes:", traci.trafficlight.getControlledLanes(tlsID=tls))
    print("Controlled Links:", traci.trafficlight.getControlledLinks(tlsID=tls))

    print("in a for:")



    # Links controlled by  a single Traffic Light
    # this will be true for all TLs
    controlled_edges = []


    for i in traci.trafficlight.getControlledLinks(tlsID=tls):
        if len(i) > 0:
            tmp = i[0][0]

            controlled_edges.append(tmp[:-2])

    print("Controlled edges:")
    for i in controlled_edges:
        print(i)

    print("\n")

    #
    cluster_nominees = []

    for i in controlled_edges:
        for j in range(0, len(clusters_edge)):
            if clusters_edge[j] == i:
                print("cluster {} is on {}!".format(j, i))
                cluster_nominees.append(j)
                # ezekbol mar lehet kovetkeztetest vonni: megvan a harom kluszter ami szobajohet, itt utankent sulyozzuk es utana váltunk fázist

    print("\n\nCluster {} has priority!\n\n".format(find_priority_edge(cluster_nominees, old_clusters, current_prio)))

    #itt vált először a sárgára, amit majd a zöld követ a current prio remelhetoleg megoldja ha ne valtson


    # city.print()

traci.close(True)
