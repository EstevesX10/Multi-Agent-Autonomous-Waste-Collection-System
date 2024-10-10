# Import necessary SPADE modules
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade

from Environment import Environment
from BinAgent import BinAgent

SIGNAL_STRENGTH = 10

class PickUpBehaviour(OneShotBehaviour):
    async def on_start(self, target):
        print(f"Truck moving to {target}")
        self.target = target

    async def run(self):
        await asyncio.wait(
            self.agent.env.distanceMatrix[self.agent._mapPosition][self.target]
        )

        self.agent._mapPosition = self.target

    async def on_end(self):
        print(f"Behaviour finished with exit code {self.exit_code}.")

# class ProximitySenderBehaviour(CyclicBehaviour):
#     def __init__(self, msg: Message, signal_dist: float):
#         super().__init__()
#         self.msg = msg
#         self.signal_dist = signal_dist

#     def bfs(self):
#         # Fetch an instance of the environment
#         env: Environment = self.agent.env

#         # Initialize a queue with the current agent's position and the current depth of the search given the node (used to perfrom BFS)
#         nodes = [(self.agent.getMapPosition(), 0)]

#         # Initialize a visited array to keep track of the already visited nodes
#         visited = [False] * env.numberNodes
#         # i = 0

#         # While we still have elements to analyse (aka inside the queue)
#         while len(nodes) != 0:
#             # Pop the next node to be analysed
#             node, depth = nodes.pop()

#             # Update its visited state on the previous array
#             visited[node] = True

#             # Check if the search has gone beyond the depth limited defined
#             if depth >= self.signal_dist:
#                 continue
            
#             # Iterate through the adjacent nodes
#             for edge in env.graph.adjsNodes(node):
#                 n = edge.endnode()
                
#                 # If the current adjacent node has already been visited, then we check the next
#                 if visited[n]:
#                     continue
                
#                 # Add the new unvisited node to the queue alongside its depth
#                 nodes.append((n, depth + edge.value.getDistance()))

#                 # Fetch the agents inside the current adjacent node
#                 content = env.graph.verts[n].getContents()
                
#                 # For each agent inside the current adjacent node, we send it a message
#                 for contentAgent in content:
#                     if isinstance(contentAgent, BinAgent):
#                         self.msg.to = contentAgent.jid.localpart + "@" + contentAgent.jid.domain
#                         # await self.send(self.msg)
#                         print(f"{self.agent.jid}\t[SENT A MESSAGE]")

#             # i += 1

#     async def run(self):
#         # Fetch an instance of the environment
#         env: Environment = self.agent.env
        
#         # CODE HERE

class ListenerBehaviour(CyclicBehaviour):
    async def run(self):
        # wait for a message for 10 seconds
        msg = await self.receive(timeout=10)
        if msg:
            # If a message has been received, then we print it
            print(f"{self.agent.jid}\t[RECEIVED MESSAGE] : {msg.body}")
            self.target = msg.body

# If the truck is in the same node as a bin then, we trigger a extraction behviour (?)
class RemoveTrash(OneShotBehaviour):
    async def run(self):
        print("[START REMOVE TRASH BEHAVIOUR]")
        # Get the current Truck Node
        currentNode = self.agent.environment.truckPositions[self.agent.jid]

        # Get agents inside the same node of the network
        availableAgents = self.agent.environment.getNodeAgents(currentNode)

        # Go trough each one of the available agents in the current node
        for nodeAgent in availableAgents:
            if isinstance(nodeAgent, BinAgent):
                # Check for a valid trash extraction
                if self.agent._validTrashExtraction(nodeAgent):
                    # Remove the trash from the bin onto the truck
                    self.agent.environment.performTrashExtraction(currentNode, nodeAgent.jid, self.agent.jid)

class TruckMovement(CyclicBehaviour):
    async def run(self):
        print("[START TRUCK BEHAVIOUR]")
        # Perceive environment data
        currentTruckPosition = self.getTruckPosition(self.agent.jid)

        # <TODO> Perform some movement and get a new node
        newNodePos = 1

        # Update the truck position insde the Environment
        self.agent.environment.updateTruckPosition(currentTruckPosition, newNodePos, self.agent.jid)

        # Communicate with air traffic control
        # await self.send_instruction_to_atc(truck_position)

    def getTruckPosition(self):
        # Access the environment object to retrieve the aircraft's position
        return self.agent.environment.getTruckPosition()

class TruckAgent(Agent):
    def __init__(
        self,
        jid: str,
        password: str,
        environment: Environment,
        verify_security: bool = False,
    ) -> None:
        super().__init__(jid, password, verify_security)
        self.env = environment

        self._currentTrashLevel = 10
        self._maxTrashCapacity = 50

        self._fueltype = 1  # 1 - Eletric || 2 - Gas / Gasoline
        self._fuelLevel = 100
        self._fuelDepletionRate = 2 * (
            1 / self._fueltype
        )  # Constant that determines how fast the truck loses its fuel

    async def setup(self):
        print(f"[SETUP] {self.jid}\n")

        # Setting up a listening behaviour
        template = Template()
        template.set_metadata("performative", "fill_level_query")
        self.add_behaviour(ListenerBehaviour(), template)

        # Setting up a Proximity sender behaviour
        # msg = Message()
        # msg.set_metadata("performative", "fill_level_query")
        # msg.body="bruhhhhh"
        # self.add_behaviour(ProximitySenderBehaviour(msg, SIGNAL_STRENGTH))

        # Setting the Truck Movement Behaviour
        self.add_behaviour(TruckMovement())

        # Add an extraction behaviour
        self.add_behaviour(RemoveTrash())

    def getMaxTrashCapacity(self) -> int:
        """
        # Description
            -> Gets the maximum trash capacity of the truck
        """
        return self._maxTrashCapacity

    def getCurrentTrashLevel(self) -> int:
        """
        # Description
            -> Gets the truck's current trash level (amount of trash the truck is currently holding)
        """
        return self._currentTrashLevel

    def getCurrentAvailableTrashCapacity(self) -> int:
        """
        # Description
            -> Get the current remaining capacity of the Truck to store trash (Maximum amount of trash it can still support)
        """
        return self.getMaxTrashCapacity() - self.getCurrentTrashLevel()

    def isEmpty(self) -> bool:
        """
        # Description
            -> Check if the truck is empty
        """
        return self.getCurrentTrashLevel() == 0

    def addTrash(self, trashAmount:int) -> None:
        """
        # Description
            -> Adds a certain amount of trash to the Truck
        """
        self._currentTrashLevel += trashAmount
    
    def removeTrash(self, trashAmount:int) -> None:
        """
        # Description
            -> Removes a certain amount of trash from the Truck
        """
        self._currentTrashLevel -= trashAmount

    # ---------------------------------------------------------------------------------------

    # ADD A CHECK FOR THE TRASH BIN AND THE TRUCK TO BE IN THE SAME POSITION INSIDE THE ENV
    def _validTrashExtraction(self, trashBin: BinAgent) -> bool:
        """
        # Description
            -> Check if a certain trash extraction from a trashBin to the Truck is valid
        """
        return (
            self.getCurrentAvailableTrashCapacity() >= trashBin.getCurrentTrashLevel()
        )

    # MAYBE CHANGE IF WE INCLUDE A ENVIRONMENT INSTANCE INSIDE THIS CLASS
    def extractBinTrash(self, trashBin: BinAgent):
        """
        # Description
            -> Performs Trash Extraction
        """
        if self._validTrashExtraction(trashBin):
            self._currentTrashLevel += trashBin.getCurrentTrashLevel()
            trashBin.cleanBin()
        return trashBin
