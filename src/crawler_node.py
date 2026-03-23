import logging
import random
import time
from typing import List

from .network import CrawlerNetwork
from .worker import CrawlerWorker

logger = logging.getLogger(__name__)

class CrawlerNode:
    def __init__(self, network: CrawlerNetwork, worker_count: int = 4):
        self.network = network
        self.workers: List[CrawlerWorker] = [CrawlerWorker(self.network) for _ in range(worker_count)]
        self.active_workers = set(self.workers)
        self.pending_tasks = []
        self.task_queue = []

    def add_task(self, task):
        self.pending_tasks.append(task)

    def run(self):
        while True:
            # Load balance tasks across available workers
            while self.pending_tasks and self.active_workers:
                task = self.pending_tasks.pop(0)
                worker = random.choice(list(self.active_workers))
                worker.execute_task(task)

            # Check worker status and handle failures
            for worker in list(self.active_workers):
                if not worker.is_alive():
                    self.active_workers.remove(worker)
                    logger.warning(f'Worker {worker} has failed. Launching replacement.')
                    new_worker = CrawlerWorker(self.network)
                    self.workers.append(new_worker)
                    self.active_workers.add(new_worker)

            # Add new tasks to the queue
            self.task_queue.extend(self.pending_tasks)
            self.pending_tasks.clear()

            # Sleep for a short time to avoid busy waiting
            time.sleep(0.1)
