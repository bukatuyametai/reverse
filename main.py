import time
import random
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from othello_rust import Color, BitboardOthello


# --- AI定義 ---

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


# --- Gameクラスの定義 ---

class Game:
    def __init__(self, black_ai_class, white_ai_class) -> None:
        # Rust側のコンストラクタ
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
                # Rust側の make_move を呼び出し
                self.othello.make_move(x, y, turn_color)
                pass_count = 0
            else:
                pass_count += 1

            # ターン交代
            turn_color = Color.WHITE if turn_color == Color.BLACK else Color.BLACK

        return self.winner()

    def winner(self) -> Optional[Color]:
        """石数を数えて勝者を判定する"""
        # Rust側は tuple (black, white) を返す
        black_count, white_count = self.othello.count_stones()

        if black_count > white_count:
            return Color.BLACK
        elif white_count > black_count:
            return Color.WHITE
        else:
            return None  # Draw


# --- メイン処理 ---

if __name__ == "__main__":
    # Rust実装なので10,000回でも高速に終わります
    num_games = 10000
    results = {"BLACK": 0, "WHITE": 0, "DRAW": 0}

    start_time = time.time()

    for i in range(num_games):
        game_manager = Game(RandomAI, YosumiAI)
        winner = game_manager.play()

        if winner == Color.BLACK:
            results["BLACK"] += 1
        elif winner == Color.WHITE:
            results["WHITE"] += 1
        else:
            results["DRAW"] += 1
        
    elapsed = time.time() - start_time

    print("-" * 40)
    print(f"対戦結果 (10,000戦):")
    print(f"  黒 (RandomAI): {results['BLACK']} 勝")
    print(f"  白 (YosumiAI): {results['WHITE']} 勝")
    print(f"  引き分け     : {results['DRAW']}")
    print("-" * 40)
    print(f"勝率 (YosumiAI): {(results['WHITE'] / num_games) * 100:.2f}%")
    print(f"総計算時間: {elapsed:.4f}s")
    print(f"1試合平均 : {elapsed / num_games:.6f}s")