from __future__ import annotations
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour
from spade.template import Template
from spade.message import Message
import asyncio
import spade

msg = Message()
msg.set_metadata("performative", "fill_level_query")


template = Template()
# template.sender = "sender1@host"
# template.to = "recv1@host"
# template.body = "Hello World"
# template.thread = "thread-id"
template.set_metadata("performative", "fill_level_query")

print(template.match(msg))