import logging
from typing import List, Type
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.agent import Agent
from Environment import Environment
from copy import copy
import os


# Agent with some utility functions
class SuperAgent(Agent):
    env: Environment
    logger: logging.Logger

    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)

        # Setup logging
        logger = logging.getLogger(jid)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(levelname)-8s - [%(name)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        # logger.setLevel(logging.DEBUG)
        logger.setLevel(os.environ.get(f"LOGLEVEL-{jid}", "DEBUG").upper())
        self.logger = logger

    async def broadcast(
        self, msg: Message, type: Type, behaviour: CyclicBehaviour
    ) -> List[str]:
        # Sends a message to all agents of a given type
        peers = []
        for jid, agent in self.env.agents.items():
            if isinstance(agent, type):
                msg.to = jid
                await behaviour.send(copy(msg))
                peers.append(jid)
        return peers
