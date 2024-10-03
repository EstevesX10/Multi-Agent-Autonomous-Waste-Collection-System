# Import necessary SPADE modules
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade

class TrashBin(Agent):
    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self._binContent = 0
        self._maxCapacity = 10
        self._mapPosition = (0,0)

    class MyBehav(CyclicBehaviour):
        async def on_start(self):
            print("[Start] Trash Bin")
            self.counter = 0

        async def run(self):
            print("Counter: {}".format(self.counter))
            self.counter += 1
            if self.counter > 3:
                self.kill(exit_code=10)
                return
            await asyncio.sleep(1)

        async def on_end(self):
            print("Behaviour finished with exit code {}.".format(self.exit_code))

    class RecvBehav(OneShotBehaviour):
        async def run(self):
            print("[TRASH BIN] receiving messages")

            msg = await self.receive(timeout=10) # wait for a message for 10 seconds
            if msg:
                print("Message received with content: {}".format(msg.body))
            else:
                print("Did not received any message after 10 seconds")

            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self):
        print(f"Hello World! I'm Trash Bin <{str(self.jid)}>")
        self.add_behaviour(self.MyBehav())
        self.add_behaviour(self.RecvBehav())
    
    def cleanBin(self):
        if self._binContent > 0:
            self._binContent = 0

    def get_position(self):
        return self._mapPosition
    
    def set_position(self, newPosition):
        self._mapPosition = newPosition
    
    def isEmpty(self):
        return self._binContent == 0

    def _validTrashDeposit(self, trash):
        return self._binContent + trash <= self._maxCapacity 

    def depositTrash(self, trash:list):
        if (self._validTrashDeposit(trash)):
            self._binContent += trash

async def main():
    # jid = input("JID> ")
    # passwd = getpass.getpass()
    # dummy = DummyAgent(jid, passwd)
    
    bin = TrashBin("admin@localhost", "password")
    bin.depositTrash(10)
    await bin.start()


if __name__ == "__main__":
    spade.run(main())