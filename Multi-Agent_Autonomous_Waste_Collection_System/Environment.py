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
import random

# from BinAgent import (BinAgent)
# from TruckAgent import (TruckAgent)

TRAFFIC_BY_TIME = [
    # time, from, to
    (0, 1, 3),
    (6, 9, 12),
    (10, 4, 5),
    (15, 4, 7),
    (19, 7, 10),
    (22, 1, 3),
]


@dataclass
class Road:
    _distance: float
    _availability: int
    _fuelConsumption: float

    def getDistance(self):
        return self._distance

    def isAvailable(self):
        return self._availability

    def getFuelConsumption(self):
        return self._fuelConsumption

    def blockRoad(self):
        self._availability = 0

    def freeRoad(self):
        self._availability = 1

    def getTravelTime(self, time: int):
        return self.getDistance() + self.trafficByTime(time)

    def trafficByTime(self, time) -> int:
        for x, start, end in reversed(TRAFFIC_BY_TIME):
            if x <= time:
                return random.randint(start, end)

        return 0


class Environment:
    def __init__(
        self, envFile: str = "./EnvironmentLayouts/Layout1.txt", useUI: bool = False
    ) -> None:
        self.roads = []
        self.numberNodes, self.graph, self.positionsUI = self.__readGraph(envFile)
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
            self.SCREEN_WIDTH = 1080
            self.SCREEN_HEIGHT = 720
            self.screen = pygame.display.set_mode(
                (self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
            )
            pygame.display.set_caption("Waste Collection System")
            self.clock = pygame.time.Clock()

            # Colors
            self.WHITE = (255, 255, 255)
            self.GREEN = (89,188,149)
            self.DARK_GREEN = (21,85,57)
            self.TURQUOISE = (29,162,165)
            self.DARK_TURQUOISE = (44,129,139)
            self.LIGHT_RED = (255, 150, 150)
            self.RED = (206,36,38)
            self.GRAY = (150, 150, 150)

            # Load and set the window icon
            self.icon = pygame.image.load("./Assets/Truck.png")
            pygame.display.set_icon(self.icon)

            # Initialize font for node labels
            self.font = pygame.font.SysFont("Arial", 15)
            self.fontBold = pygame.font.SysFont("Arial", 15, bold=True)

            # Load Agent Sprites
            self.trashBinSprite = pygame.image.load("./Assets/TrashBin.png")
            self.trashBinSprite = pygame.transform.scale(self.trashBinSprite, (30, 30))
            self.truckSprite = pygame.image.load("./Assets/TrashTruck.png")
            self.truckSprite = pygame.transform.scale(self.truckSprite, (30, 30))
            self.trashFacilitySprite = pygame.image.load("./Assets/TrashFacility.png")
            self.trashFacilitySprite = pygame.transform.scale(
                self.trashFacilitySprite, (60, 60)
            )

            # Setup graph and scale node positions
            self.updateSimulationUI()

    # Graph Related Methods

    def __readGraph(
        self, envConfiguration: str, verbose: bool = False
    ) -> Tuple[int, Graph, dict]:
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
                nodePositionsUI.update({node_id: (x, y)})

            # Read the Graph Connections
            newGraph = Graph(numberNodes)
            for line in lines[numberNodes + 1 :]:
                if len(line) == 0:
                    continue

                (
                    startNode,
                    endNode,
                    availability,
                    distance,
                    fuelConsumption,
                ) = map(int, line.split(" "))
                newRoad = Road(
                    distance,
                    bool(availability),
                    fuelConsumption,
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

    # [REMOVE]
    def draw_drop_icon(self, x, y):
        """Draws a simple drop icon at the specified (x, y) position."""
        # Draw the circular part of the drop
        pygame.draw.circle(self.screen, (0, 0, 255), (x, y), 6)

        # Draw the triangular tip of the drop
        pygame.draw.polygon(
            self.screen, (0, 0, 255), [(x, y - 6), (x - 4, y + 4), (x + 4, y + 4)]
        )

    def displayStatistics(self):
        # Define the Statistics to display
        stats = [
            (f"[Fuel Consumed]", Stats.fuel_consumed),
            (f"[Trucks Without Fuel]", Stats.trucks_without_fuel),
            (f"[Trucks Over Capacity]", Stats.trucks_over_capacity),
            (f"[Trash Collected]", Stats.trash_collected),
            (f"[Trash Deposited]", Stats.trash_deposited),
            (f"[Trash Overspill]", Stats.trash_overspill),
        ]

        # Define Padding
        paddingX, paddingY = 10, 10

        # Get the Stats informations
        statsText = f"STATISTICS"
        statsLabel = self.font.render(statsText, True, (0, 0, 0))
        statsWidth = statsLabel.get_width() * 2
        statsHeight = statsLabel.get_height() + 200

        # Create a background box for the Statistics Box
        backgroundBoxStats = pygame.Rect(
            self.SCREEN_WIDTH - statsWidth - 8 * paddingX,
            self.SCREEN_HEIGHT - statsHeight - 4*paddingY,
            statsWidth + 7 * paddingX,
            statsHeight + 3 * paddingY,
        )

        # Draw Statistics box background
        pygame.draw.rect(
            self.screen, self.GREEN, backgroundBoxStats, border_radius=8
        )
        
        # Draw Statistics box border
        pygame.draw.rect(
            self.screen, self.DARK_GREEN, backgroundBoxStats, 2, border_radius=8
        )

        # Define Initial position and line spacing
        line_spacing = 30
        y_position = backgroundBoxStats.y + paddingY + 15

        # Add the Statistics Title into the Statistics Box
        statsTitle = self.fontBold.render("[STATISTICS]", True, self.WHITE)
        statsTitlePos = statsTitle.get_rect(
            center=(backgroundBoxStats.centerx, y_position)
        )
        self.screen.blit(statsTitle, statsTitlePos)
        y_position += line_spacing

        # Add the statistics to the box
        for stat, value in stats:
            # Render the label (left-aligned)
            label_surface = self.font.render(stat, True, self.WHITE)
            label_pos = label_surface.get_rect(
                topleft=(backgroundBoxStats.x + paddingX, y_position)
            )
            
            # Render the value (right-aligned)
            value_surface = self.font.render(str(value), True, self.WHITE)
            value_pos = value_surface.get_rect(
                topright=(backgroundBoxStats.right - paddingX, y_position)
            )

            # Display the label and value on the screen
            self.screen.blit(label_surface, label_pos)
            self.screen.blit(value_surface, value_pos)

            # Update the vertical position for the next line
            y_position += line_spacing
    
    def drawEdges(self):
        # Draw edges
        for startNode in range(self.numberNodes):
            for endNode in range(self.numberNodes):
                # Get Edge
                edge = self.graph.findEdge(startNode, endNode)
                if edge is not None:
                    # Define Colors for the roads
                    roadColor = (
                        self.GRAY
                        if edge.value.isAvailable()
                        else self.LIGHT_RED
                    )
                    roadDetailsColor = (
                        self.GREEN if edge.value.isAvailable() else self.RED
                    )

                    # Get the node coordinates
                    x1, y1 = self.positionsUI[startNode]
                    x2, y2 = self.positionsUI[endNode]

                    # Drawing Lines
                    pygame.draw.line(self.screen, roadColor, (x1, y1), (x2, y2), 8)

                    # Display the Distance between them
                    x = (x2 + x1) // 2
                    y = (y2 + y1) // 2
                    distanceString = str(edge.value.getDistance())
                    distanceLabel = self.font.render(
                        distanceString, True, (255, 255, 255)
                    )

                    # Get size of the text to create the background box
                    textWidth, textHeight = distanceLabel.get_size()

                    # Define padding
                    paddingY = 4
                    paddingX = 16

                    # Create a background box for the
                    backgroundBox = pygame.Rect(
                        x - textWidth // 2 - paddingX,
                        y - textHeight // 2 - paddingY,
                        textWidth + 2 * paddingX,
                        textHeight + 2 * paddingY,
                    )

                    # Draw background box and then draw text on top
                    pygame.draw.rect(
                        self.screen, roadDetailsColor, backgroundBox, border_radius=8
                    )
                    self.screen.blit(
                        distanceLabel, (x - textWidth // 2, y - textHeight // 2)
                    )

    # FIX LATER
    def drawGraph(self):
        """Draws the entire environment: nodes, edges, trucks, and bins."""
        self.screen.fill((173, 216, 230))

        # Draw Edges
        self.drawEdges()

        # Draw nodes
        for node, (x, y) in self.positionsUI.items():
            # Define the node's box parameters
            nodeWidth = 110
            nodeHeight = 90

            # Define the container box for each node
            boxRect = pygame.Rect(
                x - nodeWidth // 2, y - nodeHeight // 2, nodeWidth, nodeHeight
            )

            # Draw the container box with a border
            pygame.draw.rect(
                self.screen, self.TURQUOISE, boxRect, border_radius=8
            )  # Light gray background
            pygame.draw.rect(
                self.screen, self.DARK_TURQUOISE, boxRect, 2, border_radius=8
            )  # Black border

            # Display the Node ID at the top of the box
            node_text = f"[Node] {node}"
            node_label = self.fontBold.render(node_text, True, self.WHITE)
            text_rect = node_label.get_rect(center=(boxRect.centerx, boxRect.y + 15))
            self.screen.blit(node_label, text_rect)

            # Position the trash bin sprite within the node container box
            bin_sprite_pos = (
                boxRect.centerx - self.trashBinSprite.get_width() // 2,
                boxRect.centery - self.trashBinSprite.get_height() // 2 + 3,
            )

            # Check if the node has a trash bin
            if node in self.binPositions.values():
                # Draw the trash bin sprite
                self.screen.blit(self.trashBinSprite, bin_sprite_pos)

                # Get the bin stats
                trashLevel, trashCapacity = self.getBinStats(node)

                # Display the trash level below the sprite
                trash_level_text = f"Trash: {trashLevel} / {trashCapacity}"
                trash_label = self.font.render(trash_level_text, True, self.WHITE)

                # Position the trash level annotation below the sprite
                trash_text_rect = trash_label.get_rect(
                    center=(
                        boxRect.centerx,
                        boxRect.centery + self.trashBinSprite.get_height() // 2 + 15,
                    )
                )
                self.screen.blit(trash_label, trash_text_rect)

            # Display the truck sprite above the node box if the node has a truck
            if node in self.truckPositions.values():
                truck_sprite_pos = (
                    boxRect.centerx - self.truckSprite.get_width() // 2,
                    boxRect.y + self.truckSprite.get_height() + nodeHeight // 2 + 10,
                )
                self.screen.blit(self.truckSprite, truck_sprite_pos)

            # Display the trash disposit facility
            if node in self.trashDeposits.values():
                trash_deposit_sprite_pos = (
                    boxRect.centerx - self.trashFacilitySprite.get_width() // 2,
                    boxRect.y - self.trashFacilitySprite.get_height(),
                )
                self.screen.blit(self.trashFacilitySprite, trash_deposit_sprite_pos)

        # Draw Statistics
        self.displayStatistics()

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

        # Updates the UI
        if self.useUI:
            self.updateSimulationUI()

    def freeRoad(self, startNode: int, endNode: int) -> None:
        self.graph.freeRoad(startNode, endNode)
        self.graph.freeRoad(endNode, startNode)

        # Updates the UI
        if self.useUI:
            self.updateSimulationUI()

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
        if self.useUI:
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

        # Updates the UI
        if self.useUI:
            self.updateSimulationUI()

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

    def getBinStats(self, nodeId: int) -> Tuple[int, int]:
        # Get all the ids from the bins inside a given node
        bins = self.getBins(nodeId)

        # Admitting that there is only one bin per nodule max
        bin = self.agents[bins[0]]

        return (bin.getCurrentTrashLevel(), bin.getTrashMaxCapacity())

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
