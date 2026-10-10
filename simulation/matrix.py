from typing import Dict, List, Optional

class Matrix:
    """Matrice complexa simpla"""

    def __init__(self, values):
        self.values: List[List[complex]] = [[complex(v) for v in row] for row in values]

    @property
    def rows(self) -> int:
        return len(self.values)

    @property
    def cols(self) -> int:
        return len(self.values[0]) if self.values else 0

    @staticmethod
    def identity(n: int) -> "Matrix":
        return Matrix([[1 if i == j else 0 for j in range(n)] for i in range(n)])

    @staticmethod
    def column(vector) -> "Matrix":
        return Matrix([[v] for v in vector])

    def multiply(self, other: "Matrix") -> "Matrix":
        if self.cols != other.rows:
            raise ValueError("Dimensiuni incompatibile pentru inmultire")
        other_cols = list(zip(*other.values))
        return Matrix(
            [[sum(a * b for a, b in zip(row, col)) for col in other_cols] for row in self.values]
        )

    def tensor(self, other: "Matrix") -> "Matrix":
        return Matrix(
            [[a * b for a in ra for b in rb] for ra in self.values for rb in other.values]
        )

    def toList(self) -> List[complex]:
        """Pentru vectori coloana: returneaza lista de amplitudini."""
        return [row[0] for row in self.values]