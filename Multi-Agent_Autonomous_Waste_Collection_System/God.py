from datetime import datetime
from SuperAgent import SuperAgent
import asyncio
from Environment import Environment
import random
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour


class GodlyBehaviour(PeriodicBehaviour):
    def __init__(self, period: float, start_at: datetime | None = None):
        super().__init__(period, start_at)

    async def blockRandomRoad(self):
        # Get the roads
        availableRoads = self.agent.env.getRoads()

        # Sample a random road from the available ones
        selectedRoad = random.sample(availableRoads, 1)

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

        asyncio.create_task(self.freeRoad(randomRoad))


class TimeBehaviour(PeriodicBehaviour):
    async def run(self):
        self.agent.env.tickTime()
        self.agent.logger.info(f"has determined its {self.agent.env.time}:00")


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
        self.time = 0

    async def setup(self):
        print(f"[SETUP] {self.jid}\n")

        # Adding a random trash generation (Every 60s)
        self.add_behaviour(GodlyBehaviour(period=60))
        self.add_behaviour(TimeBehaviour(period=30))
