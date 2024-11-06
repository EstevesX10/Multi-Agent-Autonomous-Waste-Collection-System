# Import necessary SPADE modules
from __future__ import annotations
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade
import random

from Environment import Environment
from SuperAgent import SuperAgent
from stats import Stats

TRASH_BY_TIME = [
    # time, from, to
    (0, 1, 3),
    (6, 9, 12),
    (10, 4, 5),
    (15, 4, 7),
    (19, 7, 10),
    (22, 1, 3),
]


class GenerateTrashBehaviour(PeriodicBehaviour):
    def trashByTime(self, time) -> int:
        for x, start, end in reversed(TRASH_BY_TIME):
            if x <= time:
                return random.randint(start, end)

        self.agent.logger.warning(f"{time} is not a valid time")
        return 0

    async def run(self):
        # Randomly generate trash
        generated_trash = self.trashByTime(self.agent.env.time)

        newTrashLevel = self.agent.getCurrentTrashLevel() + generated_trash
        if newTrashLevel > self.agent.getTrashMaxCapacity():
            # Trash overspill
            Stats.trash_overspill += newTrashLevel - self.agent.getTrashMaxCapacity()
            self.agent.logger.warning(
                f"Full! Capacity: {self.agent.getTrashMaxCapacity()} units."
            )
        else:
            self.agent.updateTrashLevel(newTrashLevel)
            self.agent._predictedTrash += generated_trash
            self.agent.logger.info(
                f"Generated {generated_trash} units of trash. Total now: {self.agent.getCurrentTrashLevel()} units. Predicted: {self.agent.getPredictedTrashLevel()} units."
            )


class BinAgent(SuperAgent):
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
        self._predictedTrash = self._currentTrashLevel
        # self._mapPosition = (0,0)

    async def setup(self):
        print(f"[SETUP] {self.jid}\n")

        # Adding a random trash generation (Every 30s)
        self.add_behaviour(GenerateTrashBehaviour(period=30))

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

    def getPredictedTrashLevel(self) -> int:
        return self._predictedTrash

    def decreasePredictedTrashLevel(self, amount: int) -> int:
        newAmount = self._predictedTrash - amount
        if newAmount < 0:
            self.agent.logger.warning(
                "predicted trash level is negative! Setting to 0 and continuing anyway..."
            )
        self._predictedTrash = max(newAmount, 0)
