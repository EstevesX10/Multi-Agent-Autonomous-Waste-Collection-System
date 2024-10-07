# Import necessary SPADE modules
from spade.agent import (Agent)
from spade.behaviour import (CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour)
from spade.template import (Template)
from spade.message import (Message)
import asyncio
import spade

# from .Environment import (Environment)
# from .BinAgent import (BinAgent)

class TruckAgent(Agent):
    def __init__(self, jid: str, password: str, environment, verify_security: bool = False) -> None:
        super().__init__(jid, password, verify_security)
        self.env = environment

        self._currentTrashLevel = 10
        self._maxTrashCapacity = 50

        self._fueltype = 1 # 1 - Eletric || 2 - Gas / Gasoline
        self._fuelLevel = 100
        self._fuelDepletionRate = 2 * (1 / self._fueltype) # Constant that determines how fast the truck loses its fuel
        # self._mapPosition = (0, 0)

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

    # ADD A CHECK FOR THE TRASH BIN AND THE TRUCK TO BE IN THE SAME POSITION INSIDE THE ENV
    def _validTrashExtraction(self, trashBin) -> bool:
        """
        # Description
            -> Check if a certain trash extraction from a trashBin to the Truck is valid
        """
        return self.getCurrentAvailableTrashCapacity() <= trashBin.getCurrentTrashLevel()

    # MAYBE CHANGE IF WE INCLUDE A ENVIRONMENT INSTANCE INSIDE THIS CLASS
    def extractBinTrash(self, trashBin):
        """
        # Description
            -> Performs Trash Extraction
        """
        if (self._validTrashExtraction(self, trashBin)):
            self._currentTrashLevel += trashBin.getCurrentTrashLevel()
            trashBin.cleanBin()
        return trashBin