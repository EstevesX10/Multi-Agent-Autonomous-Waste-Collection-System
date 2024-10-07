# Import necessary SPADE modules
from spade.agent import (Agent)
from spade.behaviour import (CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour)
from spade.template import (Template)
from spade.message import (Message)
import asyncio
import spade

# Maybe use a Graph
from .DataStructures import (Graph)

# from .BinAgent import (BinAgent)
# from .TruckAgent import (TruckAgent)

class Environment():
    def __init__(self) -> None:
        self.graph = Graph(10)
        self._readGraph()
    
    def _readGraph(self):
        pass
