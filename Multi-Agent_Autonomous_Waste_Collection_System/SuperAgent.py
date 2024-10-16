from typing import List, Type
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.agent import Agent
from Environment import Environment


class SuperAgent(Agent):
    env: Environment

    def broadcast(self, msg: Message, type: Type) -> List[str]:
        peers = []
        for jid, agent in self.env.agents.items():
            if isinstance(agent, type):
                msg.to = jid
                peers.append(jid)
        return peers
