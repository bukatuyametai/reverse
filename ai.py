from othello_rust import Color, BitboardOthello
from typing import Optional, List, Tuple
import random
from abc import ABC, abstractmethod

class AI(ABC):
    def __init__(self, color: Color, game: BitboardOthello) -> None:
        self.color = color
        self.game = game

    @abstractmethod
    def place(self) -> Optional[Tuple[int, int]]:
        pass

    def legal_moves(self) -> List[Tuple[int, int]]:
        """ビットボードから座標リストに変換"""
        positions = []
        # Rust側の get_legal_moves_bits を呼び出し
        legal_bits = self.game.get_legal_moves_bits(self.color)
        
        # ビットが立っている場所を座標に変換
        for i in range(64):
            if (legal_bits >> i) & 1:
                positions.append((i % 8, i // 8))
        return positions


class RandomAI(AI):
    def place(self) -> Optional[Tuple[int, int]]:
        positions = self.legal_moves()
        return random.choice(positions) if positions else None


class YosumiAI(AI):
    CORNERS = {(0, 0), (0, 7), (7, 0), (7, 7)}
    DANGER_ZONES = {
        (0, 1), (1, 0), (1, 1),
        (6, 0), (6, 1), (7, 1),
        (0, 6), (1, 6), (1, 7),
        (6, 6), (6, 7), (7, 6),
    }

    def place(self) -> Optional[Tuple[int, int]]:
        positions = self.legal_moves()
        if not positions:
            return None

        # 1. 四隅が取れるなら取る
        current_corners = [p for p in positions if p in self.CORNERS]
        if current_corners:
            return random.choice(current_corners)

        # 2. 危険地帯以外があるならそこから選ぶ
        safe_positions = [p for p in positions if p not in self.DANGER_ZONES]
        if safe_positions:
            return random.choice(safe_positions)

        # 3. 仕方なければ全候補から選ぶ
        return random.choice(positions)