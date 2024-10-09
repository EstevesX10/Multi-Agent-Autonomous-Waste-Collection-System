# Import necessary SPADE modules
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade

from Environment import Environment
from BinAgent import BinAgent

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

class ProximitySenderBehaviour(CyclicBehaviour):
    def __init__(self, msg: Message, signal_dist: float):
        super().__init__()
        self.msg = msg
        self.signal_dist = signal_dist

    async def run(self):
        env: Environment = self.agent.env

        nodes = [(self.agent.getMapPosition(), 0)]
        visited = [False] * env.numberNodes
        i = 0
        while len(nodes) != 0:
            node, depth = nodes.pop()
            visited[node] = True

            if depth >= self.signal_dist:
                continue

            for edge in env.graph.adjsNodes(node):
                n = edge.endnode()
                
                if visited[n]:
                    continue

                nodes.append((n, depth + edge.value.getDistance()))

                content = env.graph.verts[n].getContents()
                
                for a in content:
                    if isinstance(a, BinAgent):
                        self.msg.to = a.jid.localpart + "@" + a.jid.domain
                        await self.send(self.msg)
                        print("[TRUCK SENT A MESSAGE]")

            i += 1

class ListenerBehaviour(CyclicBehaviour):
    async def run(self):
        msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
        if msg:
            print("Message received with content: {}".format(msg.body))
            self.target = msg.body


class TruckAgent(Agent):
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
        self._mapPosition = 0

    async def setup(self):
        print("[setup TRUCK]")
        template = Template()
        template.set_metadata("performative", "fill_level_query")
        self.add_behaviour(ListenerBehaviour(), template)

        msg = Message()
        msg.set_metadata("performative", "fill_level_query")
        msg.body="bruhhhhh"
        self.add_behaviour(ProximitySenderBehaviour(msg, SIGNAL_STRENGTH))

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

    def getMapPosition(self) -> int:
        """
        # Description
            -> Check if the truck is empty
        """
        return self._mapPosition

    # ADD A CHECK FOR THE TRASH BIN AND THE TRUCK TO BE IN THE SAME POSITION INSIDE THE ENV
    def _validTrashExtraction(self, trashBin: BinAgent) -> bool:
        """
        # Description
            -> Check if a certain trash extraction from a trashBin to the Truck is valid
        """
        return (
            self.getCurrentAvailableTrashCapacity() <= trashBin.getCurrentTrashLevel()
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
