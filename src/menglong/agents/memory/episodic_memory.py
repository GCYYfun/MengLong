class EpisodicMemory:
    """Episodic memory class."""

    def __init__(self):
        self.memory = []

    def remember(self, event):
        """Remember an event."""
        self.memory.append(event)

    def recall(self):
        """Recall all events."""
        return self.memory

    def forget(self):
        """Forget all events."""
        self.memory = []
