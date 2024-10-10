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
