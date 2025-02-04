# Import necessary SPADE modules
import asyncio
from stats import Stats
import spade
import pygame
import random

# Import developed classes
from Environment import Environment
from Agents import TruckAgent
from Agents import BinAgent
from Agents import God
from Utils import Config

useUI = False

# Main Loop
async def main():
    # Initializing the environment
    env = Environment(envFile="./EnvironmentLayouts/Layout3.txt", useUI=useUI)
    god = God("god@localhost", "password", env)
    await god.start(auto_register=True)

    assert (
        env.graph.nverts >= Config.binCount
    ), f"{Config.binCount} bins were requested but there are only {env.graph.nverts} nodes exist"

    # Initializing the bins
    available = [i for i in range(env.graph.nverts)]
    random.shuffle(available)
    for i in range(Config.binCount):
        bin = BinAgent(f"bin{i}@localhost", "password", env, startPos=available[i])
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
    #   no, its not a problem in our code. WE ARE ABSOLUTELY SURE its a bug in spade. (we are happy to explain in more detail if necessary)
    # - catch KeyboardInterrupt: the default run catches the exception and doesnt exit because our main never returns
    #   main can not return because asyncio tasks dont keep the program alive, it just terminates
    try:
        # spade.run(main())
        spade.container.Container().run(main())
    except KeyboardInterrupt:
        Stats.print()
