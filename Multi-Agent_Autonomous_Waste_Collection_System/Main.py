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
    bin = BinAgent("bin1@localhost", "password", env)
    truck = TruckAgent("truck1@localhost", "password", env)

    env.addAgent(0, truck)
    env.addAgent(1, bin)

    env.printNodes()

    await bin.start(auto_register=True)
    await truck.start(auto_register=True)

    # #start recording the environment for further display
    # hub1.add_behaviour(HubAgent.RecordPosition(period=0.2))
    # await hub1.spawn_package(0,3)

    # await spade.wait_until_finished(drone1)
    # await drone1.stop()
    # print("drone1 agent has stoped")
    # await spade.wait_until_finished(drone2)


if __name__ == "__main__":
    spade.run(main())
