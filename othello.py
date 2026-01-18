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
        # Stoneオブジェクトを介さず、Colorを直接格納してオーバーヘッドを削減
        self.surface = [[Color.EMPTY for _ in range(8)] for _ in range(8)]
        self._setup_initial_pieces()

    def _setup_initial_pieces(self):
        self.surface[3][3] = Color.WHITE
        self.surface[4][4] = Color.WHITE
        self.surface[3][4] = Color.BLACK
        self.surface[4][3] = Color.BLACK

    def display(self) -> None:
        print("  0 1 2 3 4 5 6 7")
        for y, row in enumerate(self.surface):
            print(f"{y} " + " ".join(c.value for c in row))

    def find_replace_stone(self, x: int, y: int, attacker_color: Color) -> list:
        # 毎回判定用の色を計算せず、事前定義
        opp = Color.BLACK if attacker_color == Color.WHITE else Color.WHITE
        stones_to_flip = []

        # 8方向をタプルで定義（定数化するとより速い）
        for dx, dy in [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        ]:
            temp = []
            nx, ny = x + dx, y + dy

            # 境界チェックと相手の色の確認を1行で行う
            while 0 <= nx < 8 and 0 <= ny < 8 and self.surface[ny][nx] == opp:
                temp.append((nx, ny))
                nx += dx
                ny += dy

            # 最後に自分の色があれば、tempにある石はすべてひっくり返せる
            if (
                temp
                and 0 <= nx < 8
                and 0 <= ny < 8
                and self.surface[ny][nx] == attacker_color
            ):
                stones_to_flip.extend(temp)

        return stones_to_flip

    def place_stone(self, x: int, y: int, attacker_color: Color) -> bool:
        # can_placeを呼び出さず、直接flip判定を行うことで二重計算を防ぐ
        flip_stones = self.find_replace_stone(x, y, attacker_color)
        if not flip_stones:
            return False

        self.surface[y][x] = attacker_color
        for fx, fy in flip_stones:
            self.surface[fy][fx] = attacker_color
        return True

    def can_place_position(self, attacker_color: Color) -> list:
        # 空いているマスだけを対象にチェック
        return [
            (x, y)
            for y in range(8)
            for x in range(8)
            if self.surface[y][x] == Color.EMPTY
            and self.find_replace_stone(x, y, attacker_color)
        ]

    def winner(self) -> Optional[Color]:
        # countメソッドを使用して高速に集計
        flat_board = [cell for row in self.surface for cell in row]
        white = flat_board.count(Color.WHITE)
        black = flat_board.count(Color.BLACK)
        if white > black:
            return Color.WHITE
        if black > white:
            return Color.BLACK
        return None
