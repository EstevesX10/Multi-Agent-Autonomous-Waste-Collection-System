# Import necessary SPADE modules
import asyncio
import spade

# Import developed classes
from Environment import Environment
from TruckAgent import TruckAgent
from BinAgent import BinAgent


# Main Loop
async def main():
    # Initializing the environment
    env = Environment()

    # Initializing the Agents
    truck1 = TruckAgent("truck1@localhost", "password", env)
    truck2 = TruckAgent("truck2@localhost", "password", env)
    bin1 = BinAgent("bin1@localhost", "password", env)
    bin2 = BinAgent("bin2@localhost", "password", env)

    # Insert the Agents into the environment
    # TODO: maybe the agents should add themselves at setup to avoid anoying messages
    env.addAgent(nodeId=0, agent=truck1)
    env.addAgent(nodeId=0, agent=truck2)
    env.addAgent(nodeId=1, agent=bin1)
    env.addAgent(nodeId=2, agent=bin2)

    # Print the agents per nodes of the network
    print(env.getAgentsDistribution())

    # return

    # print(bin1.getCurrentTrashLevel())

    # Wait for the Agents to Start
    await bin1.start(auto_register=True)
    await bin2.start(auto_register=True)
    await truck1.start(auto_register=True)
    await truck2.start(auto_register=True)

    # #start recording the environment for further display
    # hub1.add_behaviour(HubAgent.RecordPosition(period=0.2))
    # await hub1.spawn_package(0,3)

    # await spade.wait_until_finished(bin1)
    # await bin1.stop()
    # print("drone1 agent has stoped")
    # await spade.wait_until_finished(truck1)

    while True:
        await asyncio.sleep(1000)


if __name__ == "__main__":
    spade.run(main())
