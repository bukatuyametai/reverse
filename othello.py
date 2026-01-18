from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

# 1. 石の状態を定義（マジックナンバーを防ぐ）
class Color(Enum):
    WHITE = "●"
    BLACK = "○"
    EMPTY = "・"


@dataclass
class Stone:
    color: Color


@dataclass
class Board:
    # 8x8の盤面。中身はStoneオブジェクトか、何もない場合はNone
    surface: List[List[Optional[Stone]]] = field(
        default_factory=lambda: [[None for _ in range(8)] for _ in range(8)]
    )

    def set_piece(self, x: int, y: int, color: Color):
        """指定した座標に石を置く（インターフェースとしての役割）"""
        self.surface[y][x] = Stone(color=color)

    def get_piece(self, x: int, y: int) -> Optional[Stone]:
        return self.surface[y][x]

    def how_many_color(self, color: Color) -> int:
        count = 0
        for row in self.surface:
            for cell in row:
                if cell is not None and cell.color == color:
                    count += 1
        return count


class Othello:
    def __init__(self) -> None:
        # 合成：OthelloはBoardを「持っている」
        self.board = Board()
        self._setup_initial_pieces()

    def _setup_initial_pieces(self):
        # 初期配置
        self.board.set_piece(3, 3, Color.WHITE)
        self.board.set_piece(4, 4, Color.WHITE)
        self.board.set_piece(3, 4, Color.BLACK)
        self.board.set_piece(4, 3, Color.BLACK)

    def display(self) -> None:
        """盤面を綺麗に表示する"""
        print("  0 1 2 3 4 5 6 7")
        for y, row in enumerate(self.board.surface):
            line = f"{y} "
            for stone in row:
                if stone:
                    line += f"{stone.color.value} "
                else:
                    line += f"{Color.EMPTY.value} "
            print(line)

    def can_place(self, x: int, y: int, attacker_color: Color) -> bool:
        # 1. 盤面の外なら置けない
        if not (0 <= x < 8 and 0 <= y < 8):
            return False

        # 2. すでに石がある場所には置けない
        if self.board.get_piece(x, y) is not None:
            return False

        # 3. 相手の石を1つ以上ひっくり返せるか
        # find_replace_stoneの結果が空でなければ置ける
        flip_stones = self.find_replace_stone(x, y, attacker_color)
        return len(flip_stones) > 0

    def find_replace_stone(self, x: int, y: int, attacker_color: Color) -> list[tuple]:
        # 8方向のベクトル (dx, dy)
        directions = [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        ]

        opponent_color = Color.WHITE if attacker_color == Color.BLACK else Color.BLACK
        stones_to_flip = []

        for dx, dy in directions:
            temp_stones = []
            nx, ny = x + dx, y + dy

            # 1. 盤面内かつ相手の石が続く限り進む
            while 0 <= nx < 8 and 0 <= ny < 8:
                target = self.board.get_piece(nx, ny)
                if target is None:  # 空マスならこの方向は失敗
                    break
                if target.color == attacker_color:  # 自分の石を見つけたら確定
                    stones_to_flip.extend(temp_stones)
                    break
                if target.color == opponent_color:  # 相手の石なら一時保存して次へ
                    temp_stones.append((nx, ny))

                nx += dx
                ny += dy

        return stones_to_flip

    def place_stone(self, x: int, y: int, attacker_color: Color) -> bool:
        if not self.can_place(x, y, attacker_color):
            return False

        flip_stones = self.find_replace_stone(x, y, attacker_color)
        self.board.set_piece(x, y, attacker_color)
        for x, y in flip_stones:
            self.board.set_piece(x, y, attacker_color)
        return True

    def can_place_position(self, attacker_color: Color) -> list[tuple]:
        positions = []
        for x in range(8):
            for y in range(8):
                if self.can_place(x, y, attacker_color):
                    positions.append((x, y))
        return positions

    def winner(self) -> Optional[Color]:
        white = self.board.how_many_color(Color.WHITE)
        black = self.board.how_many_color(Color.BLACK)

        if white > black:
            return Color.WHITE
        elif black > white:
            return Color.BLACK
        else:
            return None