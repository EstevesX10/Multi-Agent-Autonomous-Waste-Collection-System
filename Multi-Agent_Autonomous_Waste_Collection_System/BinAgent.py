# Import necessary SPADE modules
from __future__ import annotations
from spade.behaviour import PeriodicBehaviour
import random
from datetime import datetime

from Environment import Environment
from SuperAgent import SuperAgent
from stats import Stats
from config import Config

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
        # Calculates the generated trash at hour time
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
            # Bin has enough capacity
            self.agent.updateTrashLevel(newTrashLevel)
            self.agent._predictedTrash += generated_trash
            Stats.trash_generated += generated_trash
            self.agent.logger.info(
                f"Generated {generated_trash} units of trash. Total now: {self.agent.getCurrentTrashLevel()} units. Predicted: {self.agent.getPredictedTrashLevel()} units."
            )


class DestoyWhenEmptyBehaviour(PeriodicBehaviour):
    async def run(self):
        if self.agent._currentTrashLevel <= 0:
            await self.agent.stop()


class BinAgent(SuperAgent):
    def __init__(
        self,
        jid: str,
        password: str,
        environment: Environment,
        startTrash: int = 0,
        capacity: int = Config.binCapacity,
        generatesTrash: bool = True,
        startPos: int = -1,
        verify_security: bool = False,
    ) -> None:
        super().__init__(jid, password, verify_security)
        self.env = environment
        self._startPos = (
            startPos
            if startPos != -1
            else random.randint(0, len(self.env.graph.verts) - 1)
        )
        self._currentTrashLevel = startTrash
        self._maxTrashCapacity = capacity
        self._predictedTrash = self._currentTrashLevel
        self._generatesTrash = generatesTrash
        self._lastCollectTime = datetime.now()

    async def setup(self):
        self.logger.info(f"has been registed at {self._startPos}")

        self.env.addAgent(self._startPos, self)

        if self._generatesTrash:
            # Adding a random trash generation (Every 30s)
            self.add_behaviour(GenerateTrashBehaviour(period=Config.trashGenCooldown))
        else:
            self.add_behaviour(DestoyWhenEmptyBehaviour(period=30))

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

        now = datetime.now()
        Stats.bin_collection_times[str(self.jid)].append(
            (now - self._lastCollectTime).total_seconds()
        )
        self._lastCollectTime = now

    def updateTrashLevel(self, newTrashLevel: int) -> None:
        """
        # Description
            -> Updates the current bin's trash level
        """
        self._currentTrashLevel = newTrashLevel

    def getPredictedTrashLevel(self) -> int:
        return self._predictedTrash

    def decreasePredictedTrashLevel(self, amount: int):
        newAmount = self._predictedTrash - amount
        if newAmount < 0:
            self.logger.warning(
                "predicted trash level is negative! Setting to 0 and continuing anyway..."
            )
        self._predictedTrash = max(newAmount, 0)
