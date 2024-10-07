# Import necessary SPADE modules
from __future__ import (annotations)
from spade.agent import (Agent)
from spade.behaviour import (CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour)
from spade.template import (Template)
from spade.message import (Message)
import asyncio
import spade

# from .Environment import (Environment)

class BinAgent(Agent):
    def __init__(self, jid:str, password:str, environment, verify_security:bool=False) -> None:
        super().__init__(jid, password, verify_security)
        self.env = environment
        self._currentTrashLevel = 0 # Empty Bin
        self._maxTrashCapacity = 30
        self._requestTrashExtractionThreshold = 5
        # self._mapPosition = (0,0)

    class BroadcastFillLevel(CyclicBehaviour):
        async def on_start(self):
            print(f"[START] Bin Agent")

        async def run(self):
            print(f"[RUN METHOD TO BE IMPLEMENTED]")
            await asyncio.sleep(1)
            print(f"[KILLING BIN]")
            await asyncio.sleep(1)
            self.kill()

        async def on_end(self):
            print(f"Behaviour finished with exit code {self.exit_code}.")

    class RequestTrashExtraction(OneShotBehaviour):
        async def run(self):
            print("[TRASH BIN] receiving messages")

            msg = await self.receive(timeout=10) # wait for a message for 10 seconds
            if msg:
                print(f"Message received with content: {msg.body}")
            else:
                print("Did not received any message after 10 seconds")

            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self) -> None:
        print(f"Hello World! I'm Trash Bin <{str(self.jid)}>")
        self.add_behaviour(self.BroadcastFillLevel())
        self.add_behaviour(self.RequestTrashExtraction())
    
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

async def main():
    bin = BinAgent("admin@localhost", "password", "Add_Env_Here")
    print(bin.getCurrentTrashLevel())
    bin.depositTrash(10)
    print(bin.getCurrentTrashLevel())
    await bin.start()

if __name__ == "__main__":
    spade.run(main())