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

    def toggleAvailability(self):
        self._availability = 0 if self._availability == 1 else 1


class Environment:
    def __init__(self) -> None:
        self.numberNodes, self.graph = self.__readGraph(
            "./EnvironmentLayouts/Layout1.txt"
        )
        self.distanceMatrix, self.parentMatrix = self.__calculateMatrices()
        self.truckPositions = {}  # {'TruckID':'NodeID'}
        self.binPositions = {}  # {'BinID':'NodeID'}
        self.agents = {}  # {'AgentID': 'Agent Object'} - CAN I DO THIS??

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

    def _dayClock(self):
        # EVERYTIME A EVENT HAPPENS UPDATE THE TIME/CLOCK?
        pass

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

    def getNodeAgents(self, nodeId: int) -> list:
        # Fetch the agents inside a given node
        return self.graph.verts[nodeId].getAgents()

    def updateTruckPosition(
        self, oldNodePos: int, newNodePos: int, agentId: str
    ) -> None:
        # Update the Truck position
        self.graph.removeAgentNode(oldNodePos, agentId)
        self.graph.addAgentNode(newNodePos, agentId)
        self.truckPositions.update({agentId: newNodePos})

    def performTrashExtraction(self, nodeId: int, truckId: str, binId: str) -> None:
        # Perfrom trash extraction between a truck and a bin
        self.graph.performTrashExtraction(nodeId, truckId, binId)

    def getTruckPosition(self, truckId: str) -> int:
        # Get the current node, the truck is on
        return self.truckPositions[truckId]
