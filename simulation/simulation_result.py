from .matrix import Matrix
from typing import Dict

class SimulationResult:
    def __init__(self, state: Matrix, probabilities: Dict[str, float]):
        self.state = state
        self.probabilities = probabilities

    def getState(self) -> Matrix:
        return self.state

    def getProbabilities(self) -> Dict[str, float]:
        return self.probabilities