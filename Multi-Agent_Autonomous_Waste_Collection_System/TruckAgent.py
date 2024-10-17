# Import necessary SPADE modules
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade
import random

from Environment import Environment
from BinAgent import BinAgent
from SuperAgent import SuperAgent

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
        # Get the current node of the truck
        truckCurrentNode = self.agent.env.truckPositions[str(self.agent.jid)]

        # Get the bins which are inside the same node in the graph
        availableBins = [
            key
            for (key, value) in self.agent.env.binPositions.items()
            if value == truckCurrentNode
        ]

        # Go through all the truck's available bins
        for availableBin in availableBins:
            # <TODO: NOT SURE IF I SHOULD BE DOING THIS> Check if the available bin contains trash and if so, let's communicate

            if not self.agent.env.agents[availableBin].isEmpty():
                # Create a message requesting trash from the bin
                msg = Message(to=availableBin)  # The trash bin agent's address
                msg.body = "Requesting trash collection"
                await self.send(msg)
                print(f"[{str(self.agent.jid)}] Sent trash request to the bin.")

                # Wait for the bin's response
                response = await self.receive(timeout=10)  # 10-second timeout
                if response:
                    print(
                        f"[{str(self.agent.jid)}] Received response from bin: {response.body}"
                    )

                    # Simulate collecting trash
                    trashCollected = int(
                        response.body
                    )  # Assuming the bin sends the amount of trash
                    self.agent.updateTrashLevel(
                        self.agent.getCurrentTrashLevel() + trashCollected
                    )
                    print(
                        f"[{str(self.agent.jid)}] Collected {trashCollected} units of trash. Total now: {self.agent.getCurrentTrashLevel()} units."
                    )

                    # Send confirmation to the bin
                    confirm_msg = Message(to=availableBin)
                    confirm_msg.body = f"Collected {trashCollected} units"
                    await self.send(confirm_msg)
                    print(
                        f"[{str(self.agent.jid)}] Sent confirmation of collection to the bin."
                    )
                else:
                    print(f"[{str(self.agent.jid)}] No response from bin.")

class TruckMovement(CyclicBehaviour):
    async def on_start(self) -> None:
        print("[START TRUCK BEHAVIOUR]")

    async def run(self):
        # Perceive environment data
        currentTruckPosition = self._getTruckPosition()

        # <TODO> Perform some movement and get a new node
        newNodePos = 0

        # Update the truck position insde the Environment
        self.agent.env.updateTruckPosition(
            currentTruckPosition, newNodePos, str(self.agent.jid)
        )

        # Communicate with air traffic control
        # await self.send_instruction_to_atc(truck_position)

    def _getTruckPosition(self):
        # Access the environment object to retrieve the truck position
        return self.agent.env.getTruckPosition(str(self.agent.jid))

class ManagerBehaviour(CyclicBehaviour):
    # TODO: better heuristic
    def choose_bin(self):
        bins = {}
        for jid, agent in self.agent.env.agents.items():
            if isinstance(agent, BinAgent):
                bins[jid] = agent.getCurrentTrashLevel()

        choosen = max(bins.keys(), key=bins.__getitem__)
        return choosen

    async def run(self):
        bin = self.choose_bin()
        msg = Message(
            metadata={"performative": "query"},
            body=bin,
        )
        peers = await self.agent.broadcast(msg, TruckAgent, self)

        resp = await self.receive(timeout=10)
        if not resp:
            print(f"Manager {self.agent.jid} got no replies")
            return

        costs = {}
        times = {}
        cost, time = resp.body.split()
        costs[resp.sender] = cost
        times[resp.sender] = time
        for _ in range(len(peers) - 1):
            resp = await self.receive(timeout=10)
            cost, time = resp.body.split()
            costs[resp.sender] = cost
            times[resp.sender] = time

        choosen = min(costs.keys(), key=costs.__getitem__)

        msg = Message(
            to=str(choosen),
            metadata={"performative": "request"},
            body=f"{bin} {times[choosen]}",
        )
        await self.send(msg)


class AssigneeBehaviour(CyclicBehaviour):
    time: int = 0

    # TODO: this
    def calculate_cost(self, bin:str):
        # Get the road(s) between the truck and the bin
        return random.random()

    async def run(self):
        req = await self.receive(timeout=999)
        if not req:
            # Request timed out
            return

        if req.metadata["performative"] == "query":
            # Reply with the cost
            print(f"Got query from {req.sender}")
            cost = self.calculate_cost(req.body)

            resp = req.make_reply()
            resp.metadata = {"performative": "inform"}
            resp.body = f"{cost} {self.time}"
            await self.send(resp)
        elif req.metadata["performative"] == "request":
            # Add new task
            bin, time = req.body.split()
            if int(time) >= self.time:
                # Request is valid
                # TODO: add task
                print(f"{self.agent.jid} accepted {bin}")

                # TODO: maybe the manager should kill himself?
                for behaviour in self.agent.behaviours:
                    if isinstance(behaviour, ManagerBehaviour):
                        self.agent.remove_behaviour(ManagerBehaviour)
                        print(f"Removed Manager from {self.agent.jid}")
                self.time += 1
        else:
            print(f"Unexpected performative {req.performative}")


class TruckAgent(SuperAgent):
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
        # self.add_behaviour(ListenerBehaviour(), template)

        # Setting up a Proximity sender behaviour
        # msg = Message()
        # msg.set_metadata("performative", "fill_level_query")
        # msg.body="bruhhhhh"
        # self.add_behaviour(ProximitySenderBehaviour(msg, SIGNAL_STRENGTH))

        # Setting the Truck Movement Behaviour
        # self.add_behaviour(TruckMovement())

        # Add an extraction behaviour
        # self.add_behaviour(RequestTrashBehaviour())

        template = Template()
        template.set_metadata("performative", "inform")
        self.add_behaviour(ManagerBehaviour(), template)

        template = Template()
        template.set_metadata("performative", "query")
        template2 = Template()
        template2.set_metadata("performative", "request")
        self.add_behaviour(AssigneeBehaviour(), template | template2)

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

    def updateTrashLevel(self, newTrashLevel: int) -> None:
        """
        # Description
            -> Updates the currunt amount of trash in the Truck
        """
        self._currentTrashLevel = newTrashLevel

    def removeTrash(self, trashAmount: int) -> None:
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
