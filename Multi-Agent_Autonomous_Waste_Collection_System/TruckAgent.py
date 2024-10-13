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

"""
class ProximitySenderBehaviour(CyclicBehaviour):
    def __init__(self, msg: Message, signal_dist: float):
        super().__init__()
        self.msg = msg
        self.signal_dist = signal_dist

    def bfs(self):
        # Fetch an instance of the environment
        env: Environment = self.agent.env

        # Initialize a queue with the current agent's position and the current depth of the search given the node (used to perfrom BFS)
        nodes = [(self.agent.getMapPosition(), 0)]

        # Initialize a visited array to keep track of the already visited nodes
        visited = [False] * env.numberNodes
        # i = 0

        # While we still have elements to analyse (aka inside the queue)
        while len(nodes) != 0:
            # Pop the next node to be analysed
            node, depth = nodes.pop()

            # Update its visited state on the previous array
            visited[node] = True

            # Check if the search has gone beyond the depth limited defined
            if depth >= self.signal_dist:
                continue
            
            # Iterate through the adjacent nodes
            for edge in env.graph.adjsNodes(node):
                n = edge.endnode()
                
                # If the current adjacent node has already been visited, then we check the next
                if visited[n]:
                    continue
                
                # Add the new unvisited node to the queue alongside its depth
                nodes.append((n, depth + edge.value.getDistance()))

                # Fetch the agents inside the current adjacent node
                content = env.graph.verts[n].getContents()
                
                # For each agent inside the current adjacent node, we send it a message
                for contentAgent in content:
                    if isinstance(contentAgent, BinAgent):
                        self.msg.to = contentAgent.jid.localpart + "@" + contentAgent.jid.domain
                        # await self.send(self.msg)
                        print(f"{self.agent.jid}\t[SENT A MESSAGE]")

            # i += 1

    async def run(self):
        # Fetch an instance of the environment
        env: Environment = self.agent.env
        
        # CODE HERE
"""

class ListenerBehaviour(CyclicBehaviour):
    async def on_start(self):
        print("[START TRUCK LISTENER BEHAVIOUR]")

    async def run(self):
        # wait for a message for 10 seconds
        msg = await self.receive(timeout=10)
        if msg:
            # If a message has been received, then we print it
            print(f"{self.agent.jid}\t[RECEIVED MESSAGE] : {msg.body}")
            self.target = msg.body

class RequestTrashBehaviour(CyclicBehaviour):
        async def run(self):
            # Create a message requesting trash from the bin
            msg = Message(to="bin1@localhost")  # The trash bin agent's address
            msg.body = "Requesting trash collection"
            await self.send(msg)
            print(f"[{self.agent.jid.localpart}] Sent trash request to the bin.")

            # Wait for the bin's response
            response = await self.receive(timeout=10)  # 10-second timeout
            if response:
                print(f"[{self.agent.jid.localpart}] Received response from bin: {response.body}")
                
                # Simulate collecting trash
                trashCollected = int(response.body)  # Assuming the bin sends the amount of trash
                self.agent.updateTrashLevel(self.agent.getCurrentTrashLevel() + trashCollected)
                print(f"[{self.agent.jid.localpart}] Collected {trashCollected} units of trash. Total now: {self.agent.getCurrentTrashLevel()} units.")
                
                # Send confirmation to the bin
                confirm_msg = Message(to="bin1@localhost")
                confirm_msg.body = f"Collected {trashCollected} units"
                await self.send(confirm_msg)
                print(f"[{self.agent.jid.localpart}] Sent confirmation of collection to the bin.")
            else:
                print(f"[{self.agent.jid.localpart}] No response from bin.")

class TruckMovement(CyclicBehaviour):
    async def on_start(self) -> None:
        print("[START TRUCK BEHAVIOUR]")

    async def run(self):
        # Perceive environment data
        currentTruckPosition = self._getTruckPosition()

        # <TODO> Perform some movement and get a new node
        newNodePos = 0

        # Update the truck position insde the Environment
        self.agent.env.updateTruckPosition(currentTruckPosition, newNodePos, self.agent.jid.localpart)

        # Communicate with air traffic control
        # await self.send_instruction_to_atc(truck_position)

    def _getTruckPosition(self):
        # Access the environment object to retrieve the truck position
        return self.agent.env.getTruckPosition(self.agent.jid.localpart)

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
        self.add_behaviour(RequestTrashBehaviour())

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

    def updateTrashLevel(self, newTrashLevel:int) -> None:
        """
        # Description
            -> Updates the currunt amount of trash in the Truck
        """
        self._currentTrashLevel = newTrashLevel
    
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
