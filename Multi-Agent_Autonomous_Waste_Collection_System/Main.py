# Import necessary SPADE modules
import asyncio
from stats import Stats
import spade

# Import developed classes
from Environment import Environment
from TruckAgent import TruckAgent
from BinAgent import BinAgent
from God import God


# Main Loop
async def main():
    # Initializing the environment
    env = Environment()
    god = God("god@localhost", "password", env)
    await god.start(auto_register=True)

    # Initializing the Agents
    truck1 = TruckAgent("truck1@localhost", "password", env)
    truck2 = TruckAgent("truck2@localhost", "password", env)
    # truck3 = TruckAgent("truck3@localhost", "password", env)
    # truck4 = TruckAgent("truck4@localhost", "password", env)
    bin1 = BinAgent("bin1@localhost", "password", env)
    bin2 = BinAgent("bin2@localhost", "password", env)

    # Insert the Agents into the environment
    # TODO: maybe the agents should add themselves at setup to avoid anoying messages
    env.addAgent(nodeId=0, agent=truck1)
    env.addAgent(nodeId=0, agent=truck2)
    # env.addAgent(nodeId=0, agent=truck3)
    # env.addAgent(nodeId=0, agent=truck4)
    env.addAgent(nodeId=1, agent=bin1)
    env.addAgent(nodeId=2, agent=bin2)

    # Print the agents per nodes of the network
    print(env.getAgentsDistribution())

    # Wait for the Agents to Start
    await bin1.start(auto_register=True)
    await bin2.start(auto_register=True)
    await truck1.start(auto_register=True)
    await truck2.start(auto_register=True)
    # await truck3.start(auto_register=True)
    # await truck4.start(auto_register=True)

    # the main function MUST NOT RETURN!
    while True:
        await asyncio.sleep(1000)


if __name__ == "__main__":
    # We need to do this because:
    # - spade will kill random tasks for no reason and it will, obviously, lead to many many many stupid bugs we cant control
    # - catch KeyboardInterrupt: the default run catches the exception and doesnt exit
    try:
        spade.container.Container().run(main())
    except KeyboardInterrupt:
        Stats.print()
