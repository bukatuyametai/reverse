from othello import Color, Othello
from abc import ABC, abstractmethod
from typing import Optional
import random

class AI(ABC):
    def __init__(self, color: Color, game: Othello) -> None:
        self.color = color
        self.game = game
    
    @abstractmethod
    def place(self) -> Optional[tuple]:
        pass

class RandomAI(AI):
    def place(self) -> Optional[tuple]:
        positions = self.game.can_place_position(self.color)
        if not positions:
            return None
        return random.choice(positions)

class YosumiAI(AI):
    def place(self) -> Optional[tuple]:
        positions = self.game.can_place_position(self.color)
        if not positions:
            return None

        # 1. 四隅（最強の場所）
        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
        for pos in corners:
            if pos in positions:
                return pos

        # 2. 危険地帯（角の隣）を定義
        # ここに打つと相手に角を取られるリスクが高い
        danger_zones = [
            (0, 1), (1, 0), (1, 1),   # 左上角の周辺
            (0, 6), (1, 7), (1, 6),   # 右上角の周辺
            (6, 0), (7, 1), (6, 1),   # 左下角の周辺
            (6, 7), (7, 6), (6, 6)    # 右下角の周辺
        ]

        # 3. 危険地帯「以外」の場所を抽出
        safe_positions = [p for p in positions if p not in danger_zones]

        if safe_positions:
            # 危険でない場所があれば、そこからランダムに選ぶ
            return random.choice(safe_positions)
        else:
            # 危険な場所しか残っていない場合は、仕方なくそこから選ぶ
            return random.choice(positions)

if __name__ == "__main__":
    num_games = 1000
    results = {"BLACK": 0, "WHITE": 0, "DRAW": 0}

    print(f"{num_games}回の対戦を開始します...")

    for i in range(num_games):
        game = Othello()
        ai_black = RandomAI(Color.BLACK, game)
        ai_white = YosumiAI(Color.WHITE, game)
        
        turn = 0
        pass_counter = 0
        
        while pass_counter < 2:
            current_ai = ai_black if turn % 2 == 0 else ai_white
            attacker = current_ai.color
            
            position = current_ai.place()
            
            if position is None:
                pass_counter += 1
            else:
                x, y = position
                game.place_stone(x, y, attacker)
                pass_counter = 0
            
            turn += 1

        # 勝敗判定
        winner = game.winner()
        if winner == Color.BLACK:
            results["BLACK"] += 1
        elif winner == Color.WHITE:
            results["WHITE"] += 1
        else:
            results["DRAW"] += 1

    # 結果表示
    print("-" * 30)
    print(f"対戦結果 ({num_games}試合):")
    print(f"黒 (RandomAI): {results['BLACK']} 勝")
    print(f"白 (YosumiAI): {results['WHITE']} 勝")
    print(f"引き分け: {results['DRAW']}")
    print("-" * 30)
    
    win_rate = (results['WHITE'] / num_games) * 100
    print(f"YosumiAI (白) の勝率: {win_rate}%")