# Import necessary SPADE modules
from .Environment import (Environment)
import asyncio
import spade

# Main Loop
async def main():
    # Initializing the environment
    env = Environment()

    # jid = input("JID> ")
    # passwd = getpass.getpass()
    # dummy = DummyAgent(jid, passwd)
    
    # Initializing the Agents
    # drone1 = DroneAgent("drone1@localhost", "password", env1, 1, 4, 3, 2, 20) #"normal" drone
    # drone2 = DroneAgent("drone2@localhost", "password", env1, 5, 10, 10, 1, 40) #"heavy" drone more carry capacity less speed

    # hub1 = HubAgent("hub1@localhost", "password", env1, 0, 0, 0)
   
    # await drone1.start(auto_register=True)
    # await hub1.start(auto_register=True)

    # #start recording the environment for further display
    # hub1.add_behaviour(HubAgent.RecordPosition(period=0.2))
    # await hub1.spawn_package(0,3)
    
    # await spade.wait_until_finished(drone1)
    # await drone1.stop()
    # print("drone1 agent has stoped")
    # await spade.wait_until_finished(drone2)

if __name__ == "__main__":
    spade.run(main())