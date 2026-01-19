from othello_bitboard import Color, BitboardOthello
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
import random
import time

# --- AI定義 (BitboardOthelloのメソッド名に合わせました) ---


class AI(ABC):
    def __init__(self, color: Color, game: BitboardOthello) -> None:
        self.color = color
        self.game = game

    @abstractmethod
    def place(self) -> Optional[Tuple[int, int]]:
        pass

    def legal_moves(self) -> List[Tuple[int, int]]:
        positions = []
        # メソッド名を get_legal_moves_bits に変更
        legal_bits = self.game.get_legal_moves_bits(self.color)
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
        (0, 1),
        (1, 0),
        (1, 1),
        (6, 0),
        (6, 1),
        (7, 1),
        (0, 6),
        (1, 6),
        (1, 7),
        (6, 6),
        (6, 7),
        (7, 6),
    }

    def place(self) -> Optional[Tuple[int, int]]:
        positions = self.legal_moves()
        if not positions:
            return None

        current_corners = [p for p in positions if p in self.CORNERS]
        if current_corners:
            return random.choice(current_corners)

        safe_positions = [p for p in positions if p not in self.DANGER_ZONES]
        if safe_positions:
            return random.choice(safe_positions)

        return random.choice(positions)


# --- Gameクラスの定義 ---


class Game:
    def __init__(self, black_ai_class, white_ai_class) -> None:
        self.othello = BitboardOthello()
        self.black_ai = black_ai_class(Color.BLACK, self.othello)
        self.white_ai = white_ai_class(Color.WHITE, self.othello)

    def play(self) -> Optional[Color]:
        """終局まで進めて勝者を返す"""
        pass_count = 0
        turn_color = Color.BLACK

        while pass_count < 2:
            current_ai = self.black_ai if turn_color == Color.BLACK else self.white_ai
            move = current_ai.place()
            
            if move:
                x, y = move
                self.othello.make_move(x, y, turn_color)
                pass_count = 0
            else:
                pass_count += 1

            # ターン交代
            turn_color = Color.WHITE if turn_color == Color.BLACK else Color.BLACK

        return self.winner()

    def winner(self) -> Optional[Color]:
        """石数を数えて勝者を判定する"""
        black_count, white_count = self.othello.count_stones()

        if black_count > white_count:
            return Color.BLACK
        elif white_count > black_count:
            return Color.WHITE
        else:
            return None  # Draw


# --- メイン処理 ---

if __name__ == "__main__":
    num_games = 10000
    results = {"BLACK": 0, "WHITE": 0, "DRAW": 0}

    print(f"{num_games}回の対戦を開始します...")
    start_time = time.time()

    for _ in range(num_games):
        # 毎回新しいゲームインスタンスを作成
        game_manager = Game(RandomAI, YosumiAI)
        winner = game_manager.play()

        if winner == Color.BLACK:
            results["BLACK"] += 1
        elif winner == Color.WHITE:
            results["WHITE"] += 1
        else:
            results["DRAW"] += 1

    elapsed = time.time() - start_time

    print("-" * 30)
    print(
        f"対戦結果: 黒(Random) {results['BLACK']}勝 / 白(Yosumi) {results['WHITE']}勝 / 引分 {results['DRAW']}"
    )
    print(f"勝率 (YosumiAI): {(results['WHITE'] / num_games) * 100:.2f}%")
    print(f"総時間: {elapsed:.2f}s (1試合平均: {elapsed / num_games:.4f}s)")
