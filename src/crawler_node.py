import asyncio
import random
import time
from typing import List

from .message_protocol import Message, MessageType
from .peer_discovery import PeerDiscovery
from .storage import StorageManager

class CrawlerNode:
    def __init__(self, storage_manager: StorageManager, peer_discovery: PeerDiscovery):
        self.storage_manager = storage_manager
        self.peer_discovery = peer_discovery
        self.consensus_peers: List[str] = []
        self.consensus_state = {}
        self.consensus_lock = asyncio.Lock()

    async def start(self):
        await self.peer_discovery.start()
        self.consensus_peers = await self.peer_discovery.discover_peers()
        self.consensus_state = await self.fetch_consensus_state()
        self.run_consensus_loop()

    async def fetch_consensus_state(self) -> dict:
        consensus_state = {}
        for peer in self.consensus_peers:
            try:
                message = Message(MessageType.GET_CONSENSUS_STATE, {})
                response = await self.send_message_to_peer(peer, message)
                consensus_state.update(response.data)
            except Exception as e:
                print(f'Error fetching consensus state from peer {peer}: {e}')
        return consensus_state

    async def send_message_to_peer(self, peer: str, message: Message) -> Message:
        reader, writer = await asyncio.open_connection(peer.split(':')[0], int(peer.split(':')[1]))
        writer.write(message.serialize())
        await writer.drain()
        response = await Message.deserialize_from_reader(reader)
        writer.close()
        await writer.wait_closed()
        return response

    def run_consensus_loop(self):
        async def consensus_loop():
            while True:
                async with self.consensus_lock:
                    new_state = await self.fetch_consensus_state()
                    if new_state != self.consensus_state:
                        self.consensus_state = new_state
                        await self.storage_manager.update_storage(new_state)
                    await asyncio.sleep(random.uniform(10, 30))
        asyncio.create_task(consensus_loop())

    async def handle_message(self, message: Message) -> Message:
        if message.type == MessageType.GET_CONSENSUS_STATE:
            async with self.consensus_lock:
                return Message(MessageType.CONSENSUS_STATE, self.consensus_state)
        else:
            raise ValueError(f'Unknown message type: {message.type}')
