# Import necessary SPADE modules
from spade.agent import (Agent)
from spade.behaviour import (CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour)
from spade.template import (Template)
from spade.message import (Message)
import asyncio
import spade

import numpy as np

# Maybe use a Graph
from DataStructures import (Graph)

# from .BinAgent import (BinAgent)
# from .TruckAgent import (TruckAgent)

class Road():
    # Type of Value I am thinking of putting inside the connections of the graph
    def __init__(self, distance, availability, fuelConsumption, batteryConsumption) -> None:
        self._distance = distance
        self._availability = availability
        self._fuelConsumption = fuelConsumption
        self._batteryConsumption = batteryConsumption
    
    def getDistance(self):
        return self._distance
    
    def isAvailable(self):
        return self._availability
    
    def getFuelConsumption(self):
        return self._fuelConsumption
    
    def getBatteryConsumption(self):
        return self._batteryConsumption
    
    def toggleAvailability(self):
        self._availability = 0 if self._availability == 1 else 1

    def __str__(self):
        return (f"Distance = {self.getDistance()} \
                  Availability = {self.isAvailable()} \
                  Fuel Consumption = {self.getFuelConsumption()} \
                  Battery Consumption = {self.getBatteryConsumption()}")

class Environment():
    def __init__(self) -> None:
        self.numberNodes, self.graph = self.__readGraph('./EnvironmentLayouts/Layout1.txt')
        self.distanceMatrix, self.parentMatrix = self.__calculateMatrices()
        print(self.distanceMatrix)
        print(self.parentMatrix)

    def __readGraph(self, envConfiguration:str, verbose:bool=False) -> Graph:
        # Open the file in read mode
        with open(envConfiguration, 'r') as f:
            # Seperate the file contents by lines using the '\n' terminator
            lines = f.read().split('\n')
            
            # Iterate through the remaining lines while saving the given edges / roads
            for idx, line in enumerate(lines):
                if (idx == 0):
                    numberNodes = int(line)
                    newGraph = Graph(numberNodes)
                else:
                    startNode, endNode, availability, distance,fuelConsumption, batteryConsumption = map(int, line.split(' '))
                    newRoad = Road(distance, bool(availability), fuelConsumption, batteryConsumption)
                    newGraph.insertNewEdge(startNode, endNode, newRoad)

        if verbose:
            print(f"Number of Nodes Added to the Network: {newGraph.numVertices()}")
            print(f"Number of Edges Added to the Network: {newGraph.numEdges()}")

        return numberNodes, newGraph

    def __calculateMatrices(self):
        # Create an empty matrix to store all the distances between nodes in the graph
        n = self.numberNodes
        distanceMatrix = np.zeros((n, n)) # Matrix that stores the minimum distance between all pairs of nodes in the network
        parentMatrix = np.zeros((n, n)) # Matrix that stores the

        # Initializing the matrix values
        for startNode in range(n):
            for endNode in range(n):
                # Search for an edge connecting the startNode to the endNode
                edge = self.graph.findEdge(startNode, endNode)
                
                if (startNode == endNode):
                    # Update the distance matrix
                    distanceMatrix[startNode, endNode] = 0

                    # Update the parent matrix
                    parentMatrix[startNode, endNode] = 0

                elif (edge is not None and edge.getValue().isAvailable()):
                    # Get the road instance
                    road = edge.getValue()

                    # Update the distance matrix
                    distanceMatrix[startNode, endNode] = road.getDistance()
                    
                    # Update the parent matrix
                    parentMatrix[startNode, endNode] = startNode
                
                else:
                    # Update the distance matrix
                    distanceMatrix[startNode, endNode] = float('inf')

                    # Update the parent matrix
                    parentMatrix[startNode, endNode] = 0

        # Performing the Floyd-Warshal Algorithm
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if distanceMatrix[i, j] > (distanceMatrix[i, k] + distanceMatrix[k, j]):
                        distanceMatrix[i, j] = distanceMatrix[i, k] + distanceMatrix[k, j]
                        parentMatrix[i, j] = parentMatrix[k, j]

        return distanceMatrix, parentMatrix

if __name__ == "__main__":
    env = Environment()