# Import necessary SPADE modules
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade
from dataclasses import dataclass
from typing import Callable, Tuple, List, Union

import numpy as np

from DataStructures import Graph
from stats import Stats

import pygame
import networkx as nx
import random

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
    def __init__(self, useUI=False) -> None:
        self.roads = []
        self.numberNodes, self.graph, self.positionsUI = self.__readGraph(
            "./EnvironmentLayouts/Layout1.txt"
        )
        self.distanceMatrix, self.parentMatrix = self.__calculateMatrices()
        self.truckPositions = {}  # {'TruckID':'NodeID'}
        self.binPositions = {}  # {'BinID':'NodeID'}
        self.agents = {}  # {'AgentID': 'Agent Object'} - CAN I DO THIS??
        self.trashDeposits = {"trashCentral": 0}  # MAYBE USE OTHERS
        self.refuelStations = {"trashCentral": 0}  # MAYBE USE OTHERS

        self.time = 0

        self.useUI = useUI

        if self.useUI:
            # Initialize Pygame
            self.screen = pygame.display.set_mode((800, 800))
            pygame.display.set_caption("Agent Environment Visualization")
            self.clock = pygame.time.Clock()

            # Initialize font for node labels
            self.font = pygame.font.Font(None, 24)

            # Setup graph and scale node positions
            self.updateSimulationUI()

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

            # Read the positions of each node in the UI
            nodePositionsUI = {}
            for node_id in range(numberNodes):
                x, y = map(int, lines[node_id + 1].split(" "))
                nodePositionsUI.update({node_id:(x, y)})

            # Read the Graph Connections
            newGraph = Graph(numberNodes)
            for line in lines[numberNodes + 1:]:
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

        return numberNodes, newGraph, nodePositionsUI

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

    def removeTruck(self, truckId: str):
        pos = self.truckPositions[truckId]
        self.graph.removeAgentNode(pos, truckId)
        del self.agents[truckId]
        del self.truckPositions[truckId]

    # Graph UI related methods

    # FIX LATER
    def drawGraph(self):
        """Draws the entire environment: nodes, edges, trucks, and bins."""
        self.screen.fill((173, 216, 230))

        # Draw edges
        for startNode in range(self.numberNodes):
            for endNode in range(self.numberNodes):
                # Get Edge
                edge = self.graph.findEdge(startNode, endNode)
                if (edge is not None and edge.value.isAvailable()):
                    x1, y1 = self.positionsUI[startNode]
                    x2, y2 = self.positionsUI[endNode]
                    pygame.draw.line(self.screen, (150, 150, 150), (x1, y1), (x2, y2), 16)

                    # Display the Distance between them
                    x = (x2 + x1) // 2
                    y = (y2 + y1) // 2
                    distanceString = str(edge.value.getDistance())
                    distanceLabel = self.font.render(distanceString, True, (0, 0, 255))  # black text
                    t = distanceLabel.get_width() // 2
                    s = distanceLabel.get_height() // 2
                    self.screen.blit(distanceLabel, (x - t, y + 8 - s))  # Adjust positioning as needed

        # Draw nodes
        for node, (x, y) in self.positionsUI.items():
            pygame.draw.circle(self.screen, (255, 255, 255), (int(x), int(y)), 30)  # light blue
            # Render node number and draw it near the node
            label = self.font.render(str(node), True, (0, 0, 0))  # black text
            self.screen.blit(label, (x - 5, y + 20))  # Adjust positioning as needed

        # Draw trucks in red
        for truck_id, node_id in self.truckPositions.items():
            x, y = self.positionsUI[node_id]
            pygame.draw.circle(self.screen, (255, 0, 0), (int(x), int(y)), 15)  # red for trucks

        # Draw bins in green
        for bin_id, node_id in self.binPositions.items():
            x, y = self.positionsUI[node_id]
            pygame.draw.circle(self.screen, (0, 255, 0), (int(x), int(y)), 10)  # green for bins

    def updateSimulationUI(self):
        # Update the graph
        self.drawGraph()

        # Update the Pygame Display
        pygame.display.flip()

    # Road Related Methods

    def getRoads(self) -> list:
        return self.roads

    # [NOTE] THESE 2 FOLLOWING METHODS ARE NOT BEING CURRENTLY USED AND NEITHER ARE THOSE RESPECTIVE INVOLVED WITHIN THE GRAPH STRUCTURE
    def blockRoad(self, startNode: int, endNode: int) -> None:
        self.graph.blockRoad(startNode, endNode)
        self.graph.blockRoad(endNode, startNode)

    def freeRoad(self, startNode: int, endNode: int) -> None:
        self.graph.freeRoad(startNode, endNode)
        self.graph.freeRoad(endNode, startNode)

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

        # Updates the Truck Positions in the UI
        if (self.useUI):
            self.updateSimulationUI()

    def getTrucks(self, nodeId: int) -> list:
        # Initialze a list for the trucks that are inside a given node
        trucksFound = []

        # Iterate through the truck positions dictionary
        for currentTruckId, currentNodeId in self.truckPositions.items():
            if currentNodeId == nodeId:
                trucksFound.append(currentTruckId)

        # Return the trucks found
        return trucksFound

    def performTrashExtraction(
        self, nodeId: int, trashAmount: int, truckId: str, binId: str
    ) -> None:
        # Get the trash level of the bin
        node = self.graph.verts[nodeId]
        binTrashLevel = [
            self.agents[agent].getCurrentTrashLevel()
            for agent in node.getAgents()
            if agent == binId
        ][0]

        if trashAmount > binTrashLevel:
            self.agents[truckId].logger.warning(
                f"tryed to collect {trashAmount} but there is only {binTrashLevel} at {binId}"
            )
            trashAmount = binTrashLevel

        # Iterate through the agents
        for agent in node.getAgents():
            # Add the trash to the truck
            if agent == truckId:
                self.agents[agent].addTrash(trashAmount)
            # Clean the Bin with the respective Trash Amount
            elif agent == binId:
                self.agents[agent].removeTrash(trashAmount)

    def performTrashRefuel(self, nodeId: int, truckId: str) -> None:
        # Loops through the agents in the node and updates the truck's fuel
        node = self.graph.verts[nodeId]
        for agentId in node.getAgents():
            # Refuel Truck
            if agentId == truckId:
                agent = self.agents[agentId]
                agent.updateFuelLevel(agent.getMaxFuelLevel())

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

    def findPath(self, start: int, end: int) -> Union[Tuple[List[int], int, int], None]:
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

    def tickTime(self):
        self.time += 1
        self.time %= 24


# https://toxigon.com/a-star-algorithm-explained
import heapq


def a_star(start: int, goal: int, graph: Graph, heuristic: Callable[[int, int], float]):
    open_list = []
    heapq.heappush(open_list, (0, start))
    came_from = {}
    g_score = {start: 0}
    fuel_cost = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_list:
        current = heapq.heappop(open_list)[1]

        if current == goal:
            return (
                reconstruct_path(came_from, current),
                g_score[current],
                fuel_cost[current],
            )

        for neighbor in graph.adjsNodes(current):
            if not neighbor.value.isAvailable():
                continue
            tentative_g_score = g_score[current] + neighbor.value.getDistance()
            tentative_fuel = fuel_cost[current] + neighbor.value.getFuelConsumption()

            if (
                neighbor.enode not in g_score
                or tentative_g_score < g_score[neighbor.enode]
            ):
                came_from[neighbor.enode] = current
                g_score[neighbor.enode] = tentative_g_score
                fuel_cost[neighbor.enode] = tentative_fuel
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
