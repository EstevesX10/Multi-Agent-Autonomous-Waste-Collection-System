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
    bin1 = BinAgent("bin1@localhost", "password", env)
    # bin2 = BinAgent("bin2@localhost", "password", env)
    
    # Insert the Agents into the environment
    env.addAgent(nodeId=0, agent=truck1)
    env.addAgent(nodeId=1, agent=bin1)
    # env.addAgent(nodeId=1, agent=bin2)

    # Print the agents per nodes of the network
    print(env.getAgentsDistribution())

    return

    # Wait for the Agents to Start
    await bin.start(auto_register=True)
    await truck.start(auto_register=True)

    # #start recording the environment for further display
    # hub1.add_behaviour(HubAgent.RecordPosition(period=0.2))
    # await hub1.spawn_package(0,3)
    bin.stop()
    truck.stop()

    await spade.wait_until_finished(bin)
    await bin.stop()
    # print("drone1 agent has stoped")
    await spade.wait_until_finished(truck)

if __name__ == "__main__":
    spade.run(main())
