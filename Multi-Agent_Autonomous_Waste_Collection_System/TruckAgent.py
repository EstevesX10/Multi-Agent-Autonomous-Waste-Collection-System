# Import necessary SPADE modules
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade
import random
from typing import Tuple

from Environment import Environment
from BinAgent import BinAgent
from SuperAgent import SuperAgent
from stats import Stats


class Tasks:
    PICKUP = "pickup"
    REFUEL = "refuel"
    # TODO: more


class TruckMovement(CyclicBehaviour):
    async def on_start(self) -> None:
        self.agent.logger.debug("[START TRUCK MOVEMENT]")

    async def run(self):
        # Perceive environment data
        env = self.agent.env
        currentTruckPosition = self._getTruckPosition()

        # Check if I come across the trash deposit
        for locationId, nodeId in env.trashDeposits.items():
            if currentTruckPosition == nodeId:
                # Deposit Trash in the Central
                self.agent.depositTrash()

                # Refuel Truck
                self.agent.refuelTank()

        if len(self.agent.tasks) == 0:
            # Agent has no tasks
            if not any(
                isinstance(item, ManagerBehaviour) for item in self.agent.behaviours
            ):
                template = Template()
                template.set_metadata("performative", "inform")
                template2 = Template()
                template2.set_metadata("performative", "confirm")
                self.agent.add_behaviour(ManagerBehaviour(), template | template2)
                self.agent.logger.info("has no tasks. Becoming a manager.")
            await asyncio.sleep(1)
            return

        # Pop current task
        cur_task = self.agent.tasks.pop(0)
        if isinstance(cur_task, int):
            # Move to the next node
            newNodePos = cur_task

            # Get the road for the next node
            road = env.graph.findEdge(currentTruckPosition, newNodePos)
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
            self.agent.consumeFuel(road.value.getFuelConsumption())

            # Update the truck position inside the Environment
            env.updateTruckPosition(
                currentTruckPosition, newNodePos, str(self.agent.jid)
            )
            self.agent.logger.debug(f"is now at {newNodePos}")

        # PICK UP TRASH
        elif cur_task.startswith(Tasks.PICKUP):
            # Split the data and parse the trash amount
            _, trashAmount = cur_task.split(" ")
            trashAmount = int(trashAmount)

            # Get the Truck ID (formated)
            truckId = str(self.agent.jid)

            # Get the agent current node
            currentNode = env.getTruckPosition(truckId)

            # Get the first Bin in the current node
            binId = env.getBins(currentNode)[0]

            # Perform Trash Extraction
            env.performTrashExtraction(currentNode, trashAmount, truckId, binId)

            binAgent = env.agents[binId]
            self.agent.logger.info(
                f"Collected {trashAmount} units of trash. Total now: {self.agent.getCurrentTrashLevel()}/{self.agent.getMaxTrashCapacity()} units. Remaining in bin: {binAgent.getCurrentTrashLevel()}/{binAgent.getTrashMaxCapacity()}"
            )

        # REFUEL TANK
        # TODO: we do this every time the pass a central
        # even if there is no task so maybe this is not necessary
        # also there isnt a deposit task yet
        elif cur_task == Tasks.REFUEL:
            # Get the Truck ID
            truckId = str(self.agent.jid)

            # Get the agent current node
            currentNode = env.getTruckPosition(truckId)

            # Perform Trash Refueling
            self.agent.performTrashRefuel(currentNode, truckId)

            self.agent.logger.warning("TODO: refuel")

        else:
            self.agent.logger.warning(f"has unknown task: {cur_task}")

    def _getTruckPosition(self):
        # Access the environment object to retrieve the truck position
        return self.agent.env.getTruckPosition(str(self.agent.jid))


class ManagerBehaviour(CyclicBehaviour):
    def choose_bin(self) -> Tuple[str, int]:
        bins = {}
        for jid, agent in self.agent.env.agents.items():
            if isinstance(agent, BinAgent):
                bins[jid] = agent.getPredictedTrashLevel()

        # Get the top 5 entries sorted by value
        top_entries = sorted(bins.items(), key=lambda item: item[1], reverse=True)[:5]

        # Separate keys and values
        keys = [entry[0] for entry in top_entries]
        values = [entry[1] for entry in top_entries]

        # Choose a random key weighted by their values
        if sum(values) != 0:
            choosen = random.choices(keys, weights=values, k=1)[0]
        else:
            # TODO: decide what to do when all bins are empty
            choosen = keys[0]
        return choosen, bins[choosen]

    async def run(self):
        # Request costs
        bin, amount = self.choose_bin()
        if amount == 0:
            # Theres no trash to collect
            await asyncio.sleep(1)
            return

        msg = Message(
            metadata={"performative": "query"},
            body=f"{bin} {amount}",
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
                self.agent.logger.debug(
                    "manager missed some replies, continuing anyway..."
                )
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
            body=f"{bin} {amount} {times[choosen]}",
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
            self.agent.env.agents[bin]._predictedTrash -= amount
            if confirm.sender == self.agent.jid:
                self.agent.logger.debug("is no longer a manager")
                self.kill()
        elif confirm.body == "deny":
            self.agent.logger.debug(f"manager got denied from {confirm.sender}")


class AssigneeBehaviour(CyclicBehaviour):
    time: int = 0

    def add_task(self, targetId: str, amount: int) -> bool:
        env = self.agent.env

        target = self.agent.env.getBinPosition(targetId)

        # If target in mid-way then cost is zero
        if (
            self.agent.predicted_trash + amount <= self.agent.getMaxTrashCapacity()
            and target in self.agent.tasks
        ):
            index = self.agent.tasks.index(target)
            self.agent.tasks.insert(index + 1, f"{Tasks.PICKUP} {amount}")

        # Calculate path to bin
        path = env.findPath(self.agent.predicted_pos, target)
        if path is None:
            self.agent.logger.warning(
                f"has no path from predicted {self.agent.predicted_pos} to {target}"
            )
            return False
        path_bin, _, required_fuel_bin = path

        # Calculate path from bin to central
        closest_central = env.trashDeposits[
            "trashCentral"
        ]  # TODO: are there going to be more?
        path = env.findPath(target, closest_central)
        if path is None:
            self.agent.logger.warning(
                f"has no path from {target=} to the central {closest_central}"
            )
            return False
        path_refuel, _, required_fuel_refuel = path

        # If there isnt enough fuel or capacity then return to central first
        required_fuel = required_fuel_bin + required_fuel_refuel
        if (
            self.agent.predicted_fuel < required_fuel
            or self.agent.predicted_trash + amount > self.agent.getMaxTrashCapacity()
        ):
            self.agent.tasks.extend(path_refuel[1:])
            self.agent.tasks.append(Tasks.REFUEL)
            # TODO: maybe add Tasks.Deposit
            self.agent.predicted_pos = path_refuel[-1]

            # Recalculate path to bin
            path = env.findPath(self.agent.predicted_pos, target)
            if path is None:
                self.agent.logger.warning(
                    f"has to refuel/deposit at central {self.agent.predicted_pos} but then cant reach {target}"
                )
                return False
            path_bin, _, _ = path

        # Add task
        self.agent.tasks.extend(path_bin[1:])
        self.agent.tasks.append(f"{Tasks.PICKUP} {amount}")
        self.agent.predicted_pos = path_bin[-1]
        return True

    def calculate_cost(self, bin: str, amount: int) -> int:
        env = self.agent.env

        # TODO: i will forget to remove this D:
        if self.time >= 1:
            return 99999

        target = env.getBinPosition(bin)

        # If target in mid-way then cost is zero
        if (
            self.agent.predicted_trash + amount <= self.agent.getMaxTrashCapacity()
            and target in self.agent.tasks
        ):
            return 0

        # Path to bin
        path = env.findPath(self.agent.predicted_pos, target)
        if path is None:
            return 99999
        _, dist_bin, required_fuel_bin = path

        # Calculate path from bin to central
        closest_central = env.trashDeposits[
            "trashCentral"
        ]  # TODO: are there going to be more?
        path = env.findPath(target, closest_central)
        if path is None:
            return 99999
        path_refuel, dist_refuel, required_fuel_refuel = path

        # If there isnt enough fuel or capacity then return to central first
        refuel_cost = 0
        required_fuel = required_fuel_bin + required_fuel_refuel
        if (
            self.agent.predicted_fuel < required_fuel
            or self.agent.predicted_trash + amount > self.agent.getMaxTrashCapacity()
        ):
            # Recalculate path to bin
            path = env.findPath(path_refuel[-1], target)
            if path is None:
                return 99999
            _, dist_bin, _ = path

            refuel_cost = dist_refuel

        cost = refuel_cost + dist_bin

        return cost

    async def run(self):
        req = await self.receive(timeout=999)
        if not req:
            # Request timed out
            return

        if req.metadata["performative"] == "query":
            # Reply with the cost
            self.agent.logger.debug(f"got query from {req.sender}")
            bin, amount = req.body.split(" ")
            cost = self.calculate_cost(bin, int(amount))

            resp = req.make_reply()
            resp.metadata = {"performative": "inform"}
            resp.body = f"{cost} {self.time}"
            await self.send(resp)
        elif req.metadata["performative"] == "request":
            # Add new task
            bin, amount, time = req.body.split()
            resp = req.make_reply()
            resp.metadata = {"performative": "confirm"}
            if int(time) >= self.time and self.add_task(bin, int(amount)):
                # Request is valid
                self.agent.logger.info(f"accepted {bin}")
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
        self.predicted_pos = 0  # TODO: isto devia ser a posição inicial
        self.predicted_fuel = self._currentFuelLevel
        self.predicted_trash = self._currentTrashLevel

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
            self.logger.critical(
                f"tryed to collect {amount}. CurrentLevel: {self.getCurrentTrashLevel()} Capacity: {self.getMaxTrashCapacity()}. Returning to base"
            )
            # TODO: cancel everything and return to base
        else:
            self._currentTrashLevel = newTrashLevel

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
        self._currentFuelLevel -= amount
        Stats.fuel_consumed += amount

        if self._currentFuelLevel <= 0:
            # Truck is dead
            Stats.trucks_without_fuel += 1
            # TODO: redistribute tasks
            self.stop()

        return self._currentFuelLevel
