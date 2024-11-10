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

useUI = True

# Main Loop
async def main():
    # Initializing the environment
    env = Environment(useUI=useUI)
    god = God("god@localhost", "password", env)
    await god.start(auto_register=True)

    # Initializing the Agents
    truck1 = TruckAgent("truck1@localhost", "password", env)
    truck2 = TruckAgent("truck2@localhost", "password", env)
    # truck3 = TruckAgent("truck3@localhost", "password", env)
    # truck4 = TruckAgent("truck4@localhost", "password", env)
    bin1 = BinAgent("bin1@localhost", "password", env, startPos=0)
    bin2 = BinAgent("bin2@localhost", "password", env)

    # Print the agents per nodes of the network
    # print(env.getAgentsDistribution())

    # Wait for the Agents to Start
    await bin1.start(auto_register=True)
    await bin2.start(auto_register=True)
    await truck1.start(auto_register=True)
    await truck2.start(auto_register=True)
    # await truck3.start(auto_register=True)
    # await truck4.start(auto_register=True)

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
