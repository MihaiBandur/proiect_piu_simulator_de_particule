# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
from .matrix import Matrix
from typing import Dict, Optional

class SimulationResult:
    def __init__(self, state: Optional[Matrix], probabilities: Dict[str, float]):
        self.state = state  # None daca o masurare a lasat qubitii intr-un amestec de stari
        self.probabilities = probabilities

    def getState(self) -> Optional[Matrix]:
        return self.state

    def getProbabilities(self) -> Dict[str, float]:
        return self.probabilities