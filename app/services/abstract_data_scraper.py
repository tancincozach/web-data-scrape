from abc import ABC, abstractmethod

class AbstractDataScraper(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_data(self):
        pass
