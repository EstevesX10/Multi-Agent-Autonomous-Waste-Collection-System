# Import necessary SPADE modules
from __future__ import annotations
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade

from Environment import Environment

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

    class FillLevelReporterBehaviour(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            if msg:
                print("RECEIVED MESSAGE")
                response = msg.make_reply()
                response.body = str(self.agent.getCurrentTrashLevel())
                await self.send(response)
                print("Sent Reply")

    async def setup(self) -> None:
        print(f"Hello World! I'm Trash Bin <{str(self.jid)}>")

        template = Template()
        template.set_metadata("performative", "fill_level_query")
        
        self.add_behaviour(self.FillLevelReporterBehaviour(), template)

        msg = Message()
        msg.set_metadata("performative", "fill_level_query")
        msg.body="bruhhhhh"
        # self.add_behaviour(ProximitySenderBehaviour(msg, SIGNAL_STRENGTH))

        print(template.match(msg))

    def getCurrentTrashLevel(self) -> int:
        """
        # Description
            -> Get the bin's current trash level
        """
        return self._currentTrashLevel

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

    # def _checkValidTrashDeposit(self, trashFillLevel):
    #     return self._binFillLevel + trashFillLevel <= self._maxCapacity

    # def depositTrash(self, trashFillLevel):
    #     if (self._checkValidTrashDeposit(trashFillLevel)):
    #         self._binFillLevel += trashFillLevel

    # def get_position(self):
    #     return self._mapPosition

    # def set_position(self, newPosition):
    #     self._mapPosition = newPosition
