# Import necessary SPADE modules
from __future__ import annotations
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade
import random

from Environment import Environment


class GenerateTrashBehaviour(PeriodicBehaviour):
    async def run(self):
        # Randomly generate trash (e.g., between 1 and 5 units)
        if self.agent.getCurrentTrashLevel() < self.agent.getTrashMaxCapacity():
            generated_trash = random.randint(1, 5)
            # Ensure it does not exceed max capacity
            newTrashLevel = min(
                self.agent.getTrashMaxCapacity(),
                self.agent.getCurrentTrashLevel() + generated_trash,
            )
            self.agent.updateTrashLevel(newTrashLevel)
            print(
                f"[{str(self.agent.jid)}] Generated {generated_trash} units of trash. Total now: {self.agent.getCurrentTrashLevel()} units."
            )
        else:
            print(
                f"[{str(self.agent.jid)}] Full! Capacity: {self.agent.getTrashMaxCapacity()} units."
            )


class ProvideTrashBehaviour(CyclicBehaviour):
    async def run(self):
        # If the bin is not empty
        msg = await self.receive(timeout=10)  # Wait for request message from the truck

        # Only if we received a request from the Truck and if the bin contains trash, we perform trash extraction
        if msg and not self.agent.isEmpty():
            print(f"[{str(self.agent.jid)}] Received request: {msg.body}")

            # Get Available trash
            trashAvailable = self.agent.getCurrentTrashLevel()
            self.agent.updateTrashLevel(
                self.agent.getCurrentTrashLevel() - trashAvailable
            )  # Reduce the trash in the bin
            print(
                f"[{str(self.agent.jid)}] Provided {trashAvailable} units of trash. Remaining: {self.agent.getCurrentTrashLevel()} units."
            )

            # Send response back to the truck
            response = Message(to=str(msg.sender))
            response.body = str(trashAvailable)  # Send the amount of trash provided
            await self.send(response)

            # Wait for confirmation from the truck
            confirmation = await self.receive(timeout=10)
            if confirmation:
                print(
                    f"[{str(self.agent.jid)}] Received confirmation: {confirmation.body}"
                )
            else:
                print(f"[{str(self.agent.jid)}] No confirmation received")


class FillLevelReporterBehaviour(CyclicBehaviour):
    async def run(self):
        # wait for a message for 10 seconds
        msg = await self.receive(timeout=10)

        # Check if a message was received and send a reply with the bin's current trash level
        if msg:
            print(f"{self.agent.jid}\t\t[RECEIVED MESSAGE]")
            response = msg.make_reply()
            response.body = str(self.agent.getCurrentTrashLevel())
            await self.send(response)
            print(f"{self.agent.jid}\t\t[REPLY SENT]")

    async def setup(self) -> None:
        print(f"[SETUP] {str(self.jid)}\n")

        # Define a FillLevelReporterBehaviour to send the current trash level to nearby trucks
        template = Template()
        template.set_metadata("performative", "fill_level_query")
        self.add_behaviour(self.FillLevelReporterBehaviour(), template)

        msg = Message()
        msg.set_metadata("performative", "fill_level_query")
        msg.body = "bruhhhhh"
        # self.add_behaviour(ProximitySenderBehaviour(msg, SIGNAL_STRENGTH))

        print(template.match(msg))


class BinAgent(Agent):
    def __init__(
        self,
        jid: str,
        password: str,
        environment: Environment,
        verify_security: bool = False,
    ) -> None:
        super().__init__(jid, password, verify_security)
        self.env = environment
        self._currentTrashLevel = 0  # Empty Bin
        self._maxTrashCapacity = 30
        self._requestTrashExtractionThreshold = 5
        # self._mapPosition = (0,0)

    async def setup(self):
        print(f"[SETUP] {self.jid}\n")

        # Setting up a listening behaviour
        template = Template()
        template.set_metadata("performative", "fill_level_query")

        # Adding a random trash generation (Every 30s)
        self.add_behaviour(GenerateTrashBehaviour(period=30))

        # Adding a behaviour to transfer the bin's trash into a truck
        self.add_behaviour(ProvideTrashBehaviour())

    def getCurrentTrashLevel(self) -> int:
        """
        # Description
            -> Get the bin's current trash level
        """
        return self._currentTrashLevel

    def getTrashMaxCapacity(self) -> int:
        """
        # Description
            -> Get the bin's maximum trash capacity
        """
        return self._maxTrashCapacity

    def isEmpty(self) -> bool:
        """
        # Description
            -> Checks if the bin is empty
        """
        return self.getCurrentTrashLevel() == 0

    def cleanBin(self) -> None:
        """
        # Description
            -> Removes the trash from itself (from the Bin)
        """
        if not self.isEmpty():
            self._currentTrashLevel = 0

    def removeTrash(self, trashAmount: int) -> None:
        """
        # Description
            -> Removes a certain trash amount from the Bin
        """
        self._currentTrashLevel -= trashAmount

    def updateTrashLevel(self, newTrashLevel: int) -> None:
        """
        # Description
            -> Updates the current bin's trash level
        """
        self._currentTrashLevel = newTrashLevel
