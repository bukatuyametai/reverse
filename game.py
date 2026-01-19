from othello_rust import Color, BitboardOthello
from typing import Optional

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
