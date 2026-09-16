from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """
    Base class for all AI Agents.

    Every agent in the system must inherit from this class and implement:

    1. can_handle()
    2. process()
    """

    name = "Base Agent"

    @abstractmethod
    def can_handle(self, data):
        """
        Returns True if the agent can process the supplied data.
        """
        raise NotImplementedError

    @abstractmethod
    def process(self, data):
        """
        Main entry point for the agent.

        Every agent should expose its functionality through this method.
        """
        raise NotImplementedError