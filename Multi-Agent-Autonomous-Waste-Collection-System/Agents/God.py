from typing import Union
from datetime import datetime
from Utils import Config
from stats import Stats
from .TruckAgent import TruckAgent
from .SuperAgent import SuperAgent
import asyncio
from Environment import Environment
import random
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour


# This behaviour blocks and frees roads periodicaly
class GodlyBehaviour(PeriodicBehaviour):
    def __init__(self, period: float, start_at: Union[datetime, None] = None):
        super().__init__(period, start_at)

    def blockRandomRoad(self):
        # Get the roads
        availableRoads = self.agent.env.getRoads()

        # Sample a random road from the available ones
        selectedRoad = random.choice(availableRoads)

        # Block the road
        selectedRoad.blockRoad()

        # Return the Road
        return selectedRoad

    async def freeRoad(self, road):
        # Perform a Cooldown before freeing the road
        cooldown = 10
        await asyncio.sleep(cooldown)

        # Free the road
        road.freeRoad()

    async def run(self):
        # Randomly removes a road
        randomRoad = self.blockRandomRoad()
        Stats.disasters += 1

        asyncio.create_task(self.freeRoad(randomRoad))


# This behaviour makes the environment time move forward
class TimeBehaviour(PeriodicBehaviour):
    async def run(self):
        self.agent.env.tickTime()
        self.agent.logger.info(f"has determined its {self.agent.env.time}:00")


# This behaviour periodicaly destroys trucks
# and creates a new one after a cooldown
# otherwise we eventually would have no trucks left
class DestroyTruckBehaviour(PeriodicBehaviour):
    async def run(self):
        trucks = [
            agent
            for agent in self.agent.env.agents.values()
            if isinstance(agent, TruckAgent)
        ]
        if len(trucks) == 0:
            self.agent.logger.info(
                "found no trucks to destroy... and is not happy about it."
            )
            return

        # Choose a victim to destroy
        victim = random.choice(trucks)
        self.agent.logger.info(f"has unleashed its wrath on {victim.jid}")
        victim.becomeStuck(canRecover=False)
        Stats.disasters += 1

        await asyncio.sleep(Config.secondsForNewTruck)

        await TruckAgent.createTruck(self.agent.env)


class God(SuperAgent):
    def __init__(
        self,
        jid: str,
        password: str,
        environment: Environment,
        verify_security: bool = False,
    ) -> None:
        super().__init__(jid, password, verify_security)
        self.env = environment

    async def setup(self):
        # Add behaviours
        self.add_behaviour(GodlyBehaviour(period=Config.secondsBetweenDisasters))
        self.add_behaviour(TimeBehaviour(period=Config.secondsPerHour))
        self.add_behaviour(
            DestroyTruckBehaviour(period=Config.secondsBetweenTruckDeath)
        )
