# Import necessary SPADE modules
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade
from dataclasses import dataclass
from typing import Callable, Tuple, List

import numpy as np

from DataStructures import Graph
from stats import Stats

# from BinAgent import (BinAgent)
# from TruckAgent import (TruckAgent)


@dataclass
class Road:
    _distance: float
    _availability: int
    _fuelConsumption: float
    _batteryConsumption: float

    def getDistance(self):
        return self._distance

    def isAvailable(self):
        return self._availability

    def getFuelConsumption(self):
        return self._fuelConsumption

    def getBatteryConsumption(self):
        return self._batteryConsumption

    def blockRoad(self):
        self._availability = 0

    def freeRoad(self):
        self._availability = 1

    def getTravelTime(self):
        return self.getDistance()  # TODO: something better


class Environment:
    def __init__(self) -> None:
        self.numberNodes, self.graph = self.__readGraph(
            "./EnvironmentLayouts/Layout1.txt"
        )
        self.distanceMatrix, self.parentMatrix = self.__calculateMatrices()
        self.truckPositions = {}  # {'TruckID':'NodeID'}
        self.binPositions = {}  # {'BinID':'NodeID'}
        self.agents = {}  # {'AgentID': 'Agent Object'} - CAN I DO THIS??
        self.trashDeposits = {"trashCentral": 0}  # MAYBE USE OTHERS
        self.refuelStations = {"trashCentral": 0}  # MAYBE USE OTHERS
        self.roads = []

    # Graph Related Methods

    def __readGraph(
        self, envConfiguration: str, verbose: bool = False
    ) -> Tuple[int, Graph]:
        # Open the file in read mode
        with open(envConfiguration, "r") as f:
            # Seperate the file contents by lines using the '\n' terminator
            lines = f.read().split("\n")
            assert len(lines) != 0, "empty config file"

            # Iterate through the remaining lines while saving the given edges / roads
            numberNodes = int(lines[0])
            newGraph = Graph(numberNodes)
            for line in lines[1:]:
                if len(line) == 0:
                    continue

                (
                    startNode,
                    endNode,
                    availability,
                    distance,
                    fuelConsumption,
                    batteryConsumption,
                ) = map(int, line.split(" "))
                newRoad = Road(
                    distance,
                    bool(availability),
                    fuelConsumption,
                    batteryConsumption,
                )
                # Making the connections directed to both sides
                newGraph.insertNewEdge(startNode, endNode, newRoad)
                newGraph.insertNewEdge(endNode, startNode, newRoad)
                self.roads.append(newRoad)

        if verbose:
            print(f"Number of Nodes Added to the Network: {newGraph.numVertices()}")
            print(f"Number of Edges Added to the Network: {newGraph.numEdges()}")

        return numberNodes, newGraph

    def __calculateMatrices(self) -> Tuple[np.ndarray, np.ndarray]:
        # Create an empty matrix to store all the distances between nodes in the graph
        n = self.numberNodes
        distanceMatrix = np.zeros(
            (n, n)
        )  # Matrix that stores the minimum distance between all pairs of nodes in the network
        parentMatrix = np.zeros((n, n))  # Matrix that stores the

        # Initializing the matrix values
        for startNode in range(n):
            for endNode in range(n):
                # Search for an edge connecting the startNode to the endNode
                edge = self.graph.findEdge(startNode, endNode)

                if startNode == endNode:
                    # Update the distance matrix
                    distanceMatrix[startNode, endNode] = 0

                    # Update the parent matrix
                    parentMatrix[startNode, endNode] = 0

                elif edge is not None and edge.getValue().isAvailable():
                    # Get the road instance
                    road = edge.getValue()

                    # Update the distance matrix
                    distanceMatrix[startNode, endNode] = road.getDistance()

                    # Update the parent matrix
                    parentMatrix[startNode, endNode] = startNode

                else:
                    # Update the distance matrix
                    distanceMatrix[startNode, endNode] = float("inf")

                    # Update the parent matrix
                    parentMatrix[startNode, endNode] = 0

        # Performing the Floyd-Warshal Algorithm
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if distanceMatrix[i, j] > (
                        distanceMatrix[i, k] + distanceMatrix[k, j]
                    ):
                        distanceMatrix[i, j] = (
                            distanceMatrix[i, k] + distanceMatrix[k, j]
                        )
                        parentMatrix[i, j] = parentMatrix[k, j]

        return distanceMatrix, parentMatrix

    def addAgent(self, nodeId: int, agent: Agent) -> None:
        # Check if the agent already exists
        if str(agent.jid) in list(self.truckPositions.keys()) + list(
            self.binPositions.keys()
        ):
            print(
                f"[Invalid Agent] {str(agent.jid)} - Agent already in the environment!"
            )
            return

        # Update Truck Agents Positions
        if "truck" in str(agent.jid):
            self.truckPositions.update({str(agent.jid): nodeId})

        # Update Bin Agents Positions
        elif "bin" in str(agent.jid):
            self.binPositions.update({str(agent.jid): nodeId})

        # Insert the Agent into a given nodule of the network
        self.graph.addAgentNode(nodeId, str(agent.jid))

        # Save the agent instance
        self.agents.update({str(agent.jid): agent})

    # Road Related Methods

    def getRoads(self) -> list:
        return self.roads

    # [NOTE] THESE 2 FOLLOWING METHODS ARE NOT BEING CURRENTLY USED AND NEITHER ARE THOSE RESPECTIVE INVOLVED WITHIN THE GRAPH STRUCTURE
    def blockRoad(self, startNode: int, endNode: int) -> None:
        self.graph.blockRoad(startNode, endNode)
        self.graph.blockRoad(endNode, startNode)

    def freeRoad(self, startNode: int, endNode: int) -> None:
        self.graph.free(startNode, endNode)
        self.graph.free(endNode, startNode)

    # Truck Related Methods

    def getTruckPosition(self, truckId: str) -> int:
        # Get the current node, the truck is on
        return self.truckPositions[truckId]

    def updateTruckPosition(
        self, oldNodePos: int, newNodePos: int, agentId: str
    ) -> None:
        # Update the Truck position
        self.graph.removeAgentNode(oldNodePos, agentId)
        self.graph.addAgentNode(newNodePos, agentId)
        self.truckPositions.update({agentId: newNodePos})

    def getTrucks(self, nodeId: int) -> list:
        # Initialze a list for the trucks that are inside a given node
        trucksFound = []

        # Iterate through the truck positions dictionary
        for currentTruckId, currentNodeId in self.truckPositions.items():
            if currentNodeId == nodeId:
                trucksFound.append(currentTruckId)

        # Return the trucks found
        return trucksFound

    def performTrashExtraction(self, nodeId: int, truckId: str, binId: str) -> None:
        # Perfrom trash extraction between a truck and a bin
        self.graph.performTrashExtraction(nodeId, truckId, binId)

    def performTrashRefuel(self, nodeId: int, truckId: str) -> None:
        # Refuel Truck
        self.graph.performTruckRefuel(nodeId, truckId)

    def _canRefuel(self, truckId: str) -> bool:
        # Checks all the available refuel stations
        for locationId, nodeId in self.refuelStations.items():
            # If the current truck is on one of them, then it can be refueled
            if nodeId == self.truckPositions[truckId]:
                return True
        return False

    # Bin Related Methods

    def getBinPosition(self, binId: str) -> int:
        # Get the current node, the truck is on
        return self.binPositions[binId]

    def getBins(self, nodeId: int) -> list:
        # Initialze a list for the bin ids that are inside a given node
        binsFound = []

        # Iterate through the bin positions dictionary
        for currentBinId, currentNodeId in self.binPositions.items():
            if currentNodeId == nodeId:
                binsFound.append(currentBinId)

        # Return the bins found in the given node
        return binsFound

    # Task Management Methods

    def findPath(self, start: int, end: int) -> List[int] | None:
        return a_star(start, end, self.graph, lambda x, y: self.distanceMatrix[x][y])

    # Miscellanious Methods

    def getAgentsDistribution(self) -> dict:
        # Initialize a dictionary for the agents within each node
        nodes = {}

        # Loop over each node and get what contents it witholds
        for idx, node in enumerate(self.graph.verts):
            nodes.update({f"Node {idx}": node.getAgents()})

        return nodes

    def printPositions(self):
        # Printing the dictionaries with the agents positions in the graph
        print(self.truckPositions)
        print(self.binPositions)

    def getNodeAgents(self, nodeId: int) -> list:
        # Fetch the agents inside a given node
        return self.graph.verts[nodeId].getAgents()

    def _dayClock(self):
        # EVERYTIME A EVENT HAPPENS UPDATE THE TIME/CLOCK?
        pass


# https://toxigon.com/a-star-algorithm-explained
import heapq


def a_star(start: int, goal: int, graph: Graph, heuristic: Callable[[int, int], float]):
    open_list = []
    heapq.heappush(open_list, (0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_list:
        current = heapq.heappop(open_list)[1]

        if current == goal:
            return reconstruct_path(came_from, current)

        for neighbor in graph.adjsNodes(current):
            tentative_g_score = g_score[current] + neighbor.value.getDistance()

            if (
                neighbor.enode not in g_score
                or tentative_g_score < g_score[neighbor.enode]
            ):
                came_from[neighbor.enode] = current
                g_score[neighbor.enode] = tentative_g_score
                f_score[neighbor.enode] = g_score[neighbor.enode] + heuristic(
                    neighbor.enode, goal
                )
                heapq.heappush(open_list, (f_score[neighbor.enode], neighbor.enode))

    return None


def reconstruct_path(came_from, current):
    total_path = [current]
    while current in came_from:
        current = came_from[current]
        total_path.append(current)
    return total_path[::-1]
