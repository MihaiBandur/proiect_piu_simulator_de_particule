# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
class Qubit:
    def __init__(self, index: int, state: int = 0):
        self.index = index
        self.state = state

    def setState(self, state: int):
        if state not in (0, 1):
            raise ValueError("Starea unui qubit trebuie să fie 0 sau 1")
        self.state = state

    def getState(self) -> int:
        return self.state
