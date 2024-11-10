# Import necessary SPADE modules
import asyncio
from stats import Stats
import spade
import pygame

# Import developed classes
from Environment import Environment
from TruckAgent import TruckAgent
from BinAgent import BinAgent
from God import God
from config import Config

useUI = True

# Main Loop
async def main():
    # Initializing the environment
    env = Environment(useUI=useUI)
    god = God("god@localhost", "password", env)
    await god.start(auto_register=True)

    # Initializing the bins
    for i in range(Config.binCount):
        bin = BinAgent(f"bin{i}@localhost", "password", env)
        await bin.start(auto_register=True)

    # Print the agents per nodes of the network
    # print(env.getAgentsDistribution())

    # Add trucks
    for _ in range(Config.truckNumber):
        await TruckAgent.createTruck(env)

    if useUI:
        # Draw environment
        env.updateSimulationUI()

    # the main function MUST NOT RETURN!
    while True:
        await asyncio.sleep(1000)


if __name__ == "__main__":
    # Initialize Pygame
    if useUI:
        pygame.init()

    # We need to do this because:
    # - spade will kill random tasks for no reason and it will, obviously, lead to many many many stupid bugs we cant control
    # - catch KeyboardInterrupt: the default run catches the exception and doesnt exit
    try:
        spade.container.Container().run(main())
    except KeyboardInterrupt:
        Stats.print()
