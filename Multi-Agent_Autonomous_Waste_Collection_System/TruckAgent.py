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
from stats import Stats

SIGNAL_STRENGTH = 10


class Tasks:
    PICKUP = "pickup"
    REFUEL = "refuel"
    # TODO: more


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
        self.agent.logger.debug("[START TRUCK MOVEMENT]")

    async def run(self):
        # Perceive environment data
        currentTruckPosition = self._getTruckPosition()

        # Check if I come across the trash deposit
        for locationId, nodeId in self.agent.env.trashDeposits.items():
            if currentNode == nodeId:
                # Deposit Trash in the Central
                self.agent.depositTrash()

                # Refuel Truck
                self.agent.refuelTank()

        if len(self.agent.tasks) == 0:
            # Agent has no tasks
            return

        # Pop current task
        cur_task = self.agent.tasks.pop(0)
        if isinstance(cur_task, int):
            # Move to the next node
            newNodePos = cur_task

            # Get the road for the next node
            road = self.agent.env.graph.findEdge(currentTruckPosition, newNodePos)
            assert (
                road is not None
            ), f"{self.agent.jid} is at {currentTruckPosition} and is trying to go to {newNodePos} but a road does NOT exist"

            # Update stats
            Stats.truck_distance_traveled[
                str(self.agent.jid)
            ] += road.value.getDistance()

            # Get the path duration
            duration = road.value.getTravelTime()

            # Wait while the truck is moving
            await asyncio.sleep(duration)

            # Consume fuel
            self.agent.consumeFuel(road.getFuelConsumption())

            # Update the truck position inside the Environment
            self.agent.env.updateTruckPosition(
                currentTruckPosition, newNodePos, str(self.agent.jid)
            )
            self.agent.logger.debug(f"is now at {newNodePos}")

        # PICK UP TRASH
        elif Tasks.PICKUP in cur_task:
            # Split the data and parse the trash amount
            _, trashAmount = cur_task.split(' ')
            trashAmount = int(trashAmount)

            # Get the Truck ID (formated)
            truckId = str(self.agent.jid)

            # Get the agent current node
            currentNode = self.agent.env.getTruckPosition(truckId)

            # Get the first Bin in the current node
            binId = self.agent.env.getBins(currentNode)[0]

            # Perform Trash Extraction
            self.agent.env.performTrashExtraction(currentNode, trashAmount, truckId, binId)

            self.agent.logger.info(f"extracted {trashAmount} from {binId}")

        # REFUEL TANK
        elif cur_task == Tasks.REFUEL:
            # Get the Truck ID
            truckId = str(self.agent.jid)

            # Get the agent current node
            currentNode = self.agent.env.getTruckPosition(truckId)

            # Perform Trash Refueling
            self.agent.performTrashRefuel(currentNode, truckId)

            self.agent.logger.warning("TODO: refuel")

        else:
            self.agent.logger.warning(f"has unknown task: {cur_task}")

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
        # Request costs
        bin = self.choose_bin()
        msg = Message(
            metadata={"performative": "query"},
            body=bin,
        )
        self.agent.logger.debug("is broadcasting")
        peers = await self.agent.broadcast(msg, TruckAgent, self)

        # Calculate best candidate
        costs = {}
        times = {}
        for _ in range(len(peers)):
            # TODO: this can in some cases receive the confirmation msg... ?
            resp = await self.receive(timeout=10)
            if not resp:
                self.agent.logger.debug("manager missed some replies")
                break
            cost, time = resp.body.split()
            costs[resp.sender] = cost
            times[resp.sender] = time

        if len(costs) == 0:
            self.agent.logger.warning("manager got no replies")
            return

        choosen = min(costs.keys(), key=costs.__getitem__)

        # Assign task to choosen
        msg = Message(
            to=str(choosen),
            metadata={"performative": "request"},
            body=f"{bin} {times[choosen]}",
        )
        self.agent.logger.debug(f"choose {msg.to} for {bin}")
        await self.send(msg)

        # Get confirmation
        # TODO: for some unholy reason sometimes this gets CancelledError???
        # cancel comes from container.py run_container
        confirm = await self.receive(timeout=10)
        if not confirm:
            self.agent.logger.debug(
                "manager got no request confirmation. Trying again..."
            )
            return

        if confirm.body == "ok":
            self.agent.logger.debug(f"manager got confirmation from {confirm.sender}")
            if confirm.sender == self.agent.jid:
                self.agent.logger.debug("is no longer a manager")
                self.agent.remove_behaviour(self)
        elif confirm.body == "deny":
            self.agent.logger.debug(f"manager got denied from {confirm.sender}")


class AssigneeBehaviour(CyclicBehaviour):
    time: int = 0

    # TODO: what should should action be?
    def add_task(self, targetId: str, action):
        target = self.agent.env.getBinPosition(targetId)
        path = self.agent.env.findPath(self.agent.end_pos, target)
        self.agent.tasks.extend(path[1:])
        self.agent.tasks.append(action)
        self.agent.end_pos = path[-1]

    # TODO: this
    def calculate_cost(self, bin: str):
        # Get the road(s) between the truck and the bin
        return random.random()

    async def run(self):
        req = await self.receive(timeout=999)
        if not req:
            # Request timed out
            return

        if req.metadata["performative"] == "query":
            # Reply with the cost
            self.agent.logger.debug(f"got query from {req.sender}")
            cost = self.calculate_cost(req.body)

            resp = req.make_reply()
            resp.metadata = {"performative": "inform"}
            resp.body = f"{cost} {self.time}"
            await self.send(resp)
        elif req.metadata["performative"] == "request":
            # Add new task
            bin, time = req.body.split()
            resp = req.make_reply()
            resp.metadata = {"performative": "confirm"}
            if int(time) >= self.time:
                # Request is valid
                self.agent.logger.info(f"accepted {bin}")

                self.add_task(bin, Tasks.PICKUP)
                self.agent.logger.debug(f"tasks are {self.agent.tasks}")

                self.time += 1
                resp.body = "ok"
            else:
                resp.body = "deny"
            await self.send(resp)
        else:
            self.agent.logger.warning(f"Unexpected performative {req.performative}")


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
        self._currentFuelLevel = 100
        self._maxFuelCapacity = 100
        self._fuelDepletionRate = 2 * (
            1 / self._fueltype
        )  # Constant that determines how fast the truck loses its fuel

        self.tasks = []
        self.end_pos = 0  # TODO: isto devia ser a posição inicial

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
        self.add_behaviour(TruckMovement())

        # Add an extraction behaviour
        # self.add_behaviour(RequestTrashBehaviour())

        template = Template()
        template.set_metadata("performative", "inform")
        template2 = Template()
        template2.set_metadata("performative", "confirm")
        self.add_behaviour(ManagerBehaviour(), template | template2)

        template = Template()
        template.set_metadata("performative", "query")
        template2 = Template()
        template2.set_metadata("performative", "request")
        self.add_behaviour(AssigneeBehaviour(), template | template2)

    # Getters

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

    def getCurrentFuelLevel(self) -> int:
        """
        # Description
            -> Get the current fuel level of the truck
        """
        return self._currentFuelLevel

    def getMaxFuelLevel(self):
        """
        # Description
            -> Get the maximum fuel capacity of the Truck
        """
        return self._maxFuelCapacity

    def isEmpty(self) -> bool:
        """
        # Description
            -> Check if the truck is empty
        """
        return self.getCurrentTrashLevel() == 0

    # Setters

    def addTrash(self, amount: int) -> int:
        newTrashLevel = self.getCurrentTrashLevel() + amount
        if newTrashLevel > self.getMaxTrashCapacity():
            # Over capacity
            Stats.trucks_over_capacity += 1
            self.agent.logger.critical(
                f"tryed to collect {amount}. CurrentLevel: {self.getCurrentTrashLevel()} Capacity: {self.getTrashMaxCapacity()}. Returning to base"
            )
            # TODO: cancel everything and return to base
        else:
            self._currentTrashLevel = newTrashLevel
            self.logger.info(
                f"Collected {amount} units of trash. Total now: {self.getCurrentTrashLevel()} units."
            )

        return self._currentTrashLevel

    def cleanTruck(self):
        # Clean the truck by emptying its trash depposit
        self._currentTrashLevel = 0

    def depositTrash(self) -> None:
        # Get current trash level
        currentTrashLevel = self.getCurrentTrashLevel()

        # Update Stats
        Stats.trash_deposited += currentTrashLevel

        # Clean Truck
        self.cleanTruck()

    def refuelTank(self):
        # Refuels the truck tank
        self._currentFuelLevel = self.getMaxFuelLevel()

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

    def consumeFuel(self, amount: int) -> int:
        self._fuelLevel -= amount
        Stats.fuel_consumed += amount

        if self._fuelLevel <= 0:
            # Truck is dead
            Stats.trucks_without_fuel += 1
            # TODO: redistribute tasks
            self.stop()

        return self._fuelLevel
