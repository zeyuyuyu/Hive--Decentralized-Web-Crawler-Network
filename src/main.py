import os
import asyncio
from hive.agent import Agent
from hive.swarm import Swarm
from hive.governance import GovernanceProtocol

# Initialize the Hive network
swarm = Swarm()
governance = GovernanceProtocol(swarm)

async def main():
    # Spawn new agents and join the swarm
    agent_1 = Agent(swarm, governance)
    agent_2 = Agent(swarm, governance)
    agent_3 = Agent(swarm, governance)
    await asyncio.gather(agent_1.start(), agent_2.start(), agent_3.start())

    # Coordinate the swarm activities
    await swarm.coordinate()

if __name__ == "__main__":
    asyncio.run(main())