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
        # 四隅の座標
        vip_places = [(0, 0), (0, 7), (7, 0), (7, 7)]
        positions = self.game.can_place_position(self.color)
        if not positions:
            return None
        
        # 四隅に打てるなら優先的に打つ
        for vip_place in vip_places:
            if vip_place in positions:
                return vip_place
            
        return random.choice(positions)

if __name__ == "__main__":
    game = Othello()
    print("--- 初期状態 ---")
    game.display()

    turn = 0
    pass_counter = 0
    # インスタンス作成
    ai_black = RandomAI(Color.BLACK, game)
    ai_white = YosumiAI(Color.WHITE, game)

    while pass_counter < 2:
        # 現在のターンがどちらか判定
        current_ai = ai_black if turn % 2 == 0 else ai_white
        attacker = current_ai.color
        
        position = current_ai.place()

        if position is None:
            print(f"{attacker.name} は置ける場所がないためパスしました。")
            pass_counter += 1
        else:
            x, y = position
            print(f"{attacker.name} が {x},{y} に設置")
            game.place_stone(x, y, attacker)
            game.display()
            # 石を置けたらパスのカウントをリセット
            pass_counter = 0
        
        turn += 1

    # ゲーム終了後の判定
    print("--- ゲーム終了 ---")
    winner = game.winner()
    if winner == Color.WHITE:
        print("白の勝ち")
    elif winner == Color.BLACK:
        print("黒の勝ち")
    else:
        print("引き分け")