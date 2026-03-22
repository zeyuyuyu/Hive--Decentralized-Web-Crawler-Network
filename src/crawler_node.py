import zmq
import json
import time
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class CrawlTask:
    url: str
    depth: int
    timestamp: float
    parent_url: str = ''

class CrawlerNode:
    def __init__(self, node_id: str, coordinator_address: str = 'tcp://localhost:5555'):
        self.node_id = node_id
        self.context = zmq.Context()
        self.task_socket = self.context.socket(zmq.DEALER)
        self.task_socket.setsockopt_string(zmq.IDENTITY, node_id)
        self.task_socket.connect(coordinator_address)
        
        self.active_tasks: Dict[str, CrawlTask] = {}
        self.results_cache: List[Dict] = []
        
    def request_task(self) -> None:
        """Request a new crawl task from the coordinator"""
        message = {'type': 'request_task', 'node_id': self.node_id}
        self.task_socket.send_json(message)

    def submit_result(self, task: CrawlTask, extracted_urls: List[str], content_hash: str) -> None:
        """Submit crawl results back to coordinator"""
        result = {
            'type': 'submit_result',
            'node_id': self.node_id,
            'task_url': task.url,
            'extracted_urls': extracted_urls,
            'content_hash': content_hash,
            'timestamp': time.time()
        }
        self.task_socket.send_json(result)

    def handle_assigned_task(self, task_data: Dict) -> None:
        """Process a newly assigned crawl task"""
        task = CrawlTask(
            url=task_data['url'],
            depth=task_data['depth'],
            timestamp=time.time(),
            parent_url=task_data.get('parent_url', '')
        )
        self.active_tasks[task.url] = task
        # Crawling logic would go here
        # For now just simulate some work
        time.sleep(1)
        self.submit_result(task, ['http://example.com/1', 'http://example.com/2'], 'fake_hash')

    def run(self) -> None:
        """Main event loop for the crawler node"""
        self.request_task()
        
        while True:
            try:
                message = self.task_socket.recv_json(flags=zmq.NOBLOCK)
                if message['type'] == 'assign_task':
                    self.handle_assigned_task(message['task'])
                    self.request_task()  # Request another task when done
            except zmq.Again:
                # No message available
                time.sleep(0.1)
            except Exception as e:
                print(f'Error in crawler node {self.node_id}: {str(e)}')
                time.sleep(1)

    def shutdown(self) -> None:
        """Clean shutdown of the crawler node"""
        self.task_socket.close()
        self.context.term()

if __name__ == '__main__':
    import uuid
    node = CrawlerNode(str(uuid.uuid4()))
    try:
        node.run()
    except KeyboardInterrupt:
        node.shutdown()