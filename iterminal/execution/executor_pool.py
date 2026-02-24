"""Centralized executor pool management."""
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Optional
import logging


logger = logging.getLogger(__name__)


class ExecutorPool:
    """Centralized management of thread and process executors."""
    
    _instance: Optional["ExecutorPool"] = None
    
    def __init__(self, thread_count: int = 16, process_count: int = 2):
        self.thread_count = thread_count
        self.process_count = process_count
        self.thread_executor: Optional[ThreadPoolExecutor] = None
        self.process_executor: Optional[ProcessPoolExecutor] = None
        self._initialized = False
    
    @classmethod
    def get_instance(cls, thread_count: int = 16, process_count: int = 2) -> "ExecutorPool":
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = cls(thread_count, process_count)
        return cls._instance
    
    def initialize(self) -> None:
        """Initialize executors."""
        if self._initialized:
            return
        
        try:
            self.thread_executor = ThreadPoolExecutor(
                max_workers=self.thread_count,
                thread_name_prefix="iterminal-"
            )
            self.process_executor = ProcessPoolExecutor(
                max_workers=self.process_count
            )
            self._initialized = True
            logger.info(
                f"ExecutorPool initialized: {self.thread_count} threads, "
                f"{self.process_count} processes"
            )
        except Exception as e:
            logger.error(f"Failed to initialize ExecutorPool: {e}")
            raise
    
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown executors."""
        if self.thread_executor:
            self.thread_executor.shutdown(wait=wait)
            logger.info("ThreadExecutor shutdown")
        
        if self.process_executor:
            self.process_executor.shutdown(wait=wait)
            logger.info("ProcessExecutor shutdown")
        
        self._initialized = False
    
    def get_thread_executor(self) -> ThreadExecutor:
        """Get thread executor."""
        if not self._initialized:
            self.initialize()
        return self.thread_executor
    
    def get_process_executor(self) -> ProcessPoolExecutor:
        """Get process executor."""
        if not self._initialized:
            self.initialize()
        return self.process_executor
    
    def __enter__(self):
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


def get_executor_pool() -> ExecutorPool:
    """Get global executor pool instance."""
    return ExecutorPool.get_instance()
