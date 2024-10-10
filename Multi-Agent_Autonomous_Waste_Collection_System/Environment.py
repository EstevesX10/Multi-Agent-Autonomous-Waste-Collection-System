# Import necessary SPADE modules
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from DataStructures import Graph

from BinAgent import (BinAgent)
from TruckAgent import (TruckAgent)

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

    def toggleAvailability(self):
        self._availability = 0 if self._availability == 1 else 1

class Environment:
    def __init__(self) -> None:
        self.numberNodes, self.graph = self.__readGraph(
            "./EnvironmentLayouts/Layout1.txt"
        )
        self.distanceMatrix, self.parentMatrix = self.__calculateMatrices()
        self.truckPositions = {} # {'TruckID':'NodeID'}
        self.binPositions = {} # {'BinID':'NodeID'}

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

    def printNodes(self) -> None:
        # Loop over each node and print what contents it witholds
        for node in self.graph.verts:
            print(node.getAgents())

    # TODO: Fix the way we are saving the agents in the environment so that we do not need to pass an instance of a Agent
    # Maybe simply use the Agents jid's to mark the agent position

    def addAgent(self, nodeId:int, agent:Agent) -> None:
        # Update Truck Agents Positions
        if isinstance(agent, TruckAgent):
            self.truckPositions.update({agent.jid:nodeId})

        # Update Bin Agents Positions
        elif isinstance(agent, BinAgent):
            self.binPositions.update({agent.jid:nodeId})

        # Insert the Agent into a given nodule of the network
        self.graph.addAgentNode(nodeId, agent)

    def updateTruckPosition(self, oldNodePos:int, newNodePos:int, agent:Agent) -> None:
        self.graph.removeAgentNode(oldNodePos, agent.jid)
        self.graph.addAgentNode(newNodePos, agent.jid)
        self.truckPositions.update({agent.jid:newNodePos})

    def getTruckPosition(self, truckId):
        return self.truckPositions[truckId]