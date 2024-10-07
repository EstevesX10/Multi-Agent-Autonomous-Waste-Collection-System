# Import necessary SPADE modules
from spade.agent import (Agent)
from spade.behaviour import (CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour)
from spade.template import (Template)
from spade.message import (Message)
import asyncio
import spade

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
    
    def getAvailability(self):
        return self._availability
    
    def getFuelConsumption(self):
        return self._fuelConsumption
    
    def getBatteryConsumption(self):
        return self._batteryConsumption
    
    def toggleAvailability(self):
        self._availability = 0 if self._availability == 1 else 1

class Environment():
    def __init__(self) -> None:
        self.graph = self._readGraph('./EnvironmentLayouts/Layout1.txt')

    def _readGraph(self, envConfiguration:str) -> Graph:
        # Open the file in read mode
        with open(envConfiguration, 'r') as f:
            # Seperate the 
            lines = f.read().split('\n')
            
            for idx, line in enumerate(lines):
                if (idx == 0):
                    numberNodes = int(line)
                    self.graph = Graph(numberNodes)
                else:
                    startNode, endNode, distance, availability, fuelConsumption, batteryConsumption = map(int, line.split(' '))
                    newRoad = Road(distance, availability, fuelConsumption, batteryConsumption)
                    self.graph.insertNewEdge(startNode, endNode, newRoad)

        print(f"Number of Nodes: {self.graph.numVertices()}")
        print(f"Number of Edges: {self.graph.numEdges()}")

if __name__ == "__main__":
    env = Environment()