from dataclasses import dataclass, field
from typing import List, Optional
from pprint import pprint

@dataclass
class Board:
    # List[List[Optional[int]]] は「数値またはNoneが入ったリストのリスト」という意味
    surface: List[List[Optional[int]]] = field(
        default_factory=lambda: [[None for _ in range(8)] for _ in range(8)]
    )

    def set_piece(self, x: int, y: int, color: int):
        self.surface[y][x] = color

    def get_piece(self, x: int, y: int):
        return self.surface[y][x]

class Othello:
    def __init__(self) -> None:
        # 継承ではなく、Boardオブジェクトを「持つ（合成）」
        self.board = Board()
        
        # 初期配置
        self.board.set_piece(3, 3, 1)
        self.board.set_piece(4, 4, 1)
        self.board.set_piece(3, 4, 0)
        self.board.set_piece(4, 3, 0)
    
    def display(self) -> None:
        pprint(self.board)

if __name__ == "__main__":
    game = Othello()
    game.display()