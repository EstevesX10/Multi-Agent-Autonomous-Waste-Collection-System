import getpass
import spade

class DummyAgent(spade.agent.Agent):
    async def setup(self):
        print(f"Hello World! I'm agent {str(self.jid)}")


async def main():
    # jid = input("JID> ")
    # passwd = getpass.getpass()
    # dummy = DummyAgent(jid, passwd)
    
    dummy = DummyAgent("admin@localhost", "password")
    await dummy.start()


if __name__ == "__main__":
    spade.run(main())
