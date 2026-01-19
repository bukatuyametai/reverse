from enum import Enum
from typing import Tuple

class Color(Enum):
    BLACK = 0
    WHITE = 1

class BitboardOthello:
    def __init__(self):
        # 座標系: LSB(2^0) = (0,0) 左上, MSB(2^63) = (7,7) 右下
        # 初期配置
        # (3, 3) = index 27, (4, 3) = index 28
        # (3, 4) = index 35, (4, 4) = index 36
        # 白: (3,3), (4,4) -> (1<<27) | (1<<36)
        # 黒: (4,3), (3,4) -> (1<<28) | (1<<35)
        self.white = 0x0000001008000000
        self.black = 0x0000000810000000

    def make_move(self, x: int, y: int, color: Color) -> bool:
        """指定した位置に石を置く。成功すればTrue、失敗ならFalse"""
        # 範囲外チェック
        if not (0 <= x < 8 and 0 <= y < 8):
            return False

        pos = 1 << (y * 8 + x)
        
        # 1. 既に石がある場所には置けない (最重要ガード)
        if (self.black | self.white) & pos:
            return False
            
        # 2. ひっくり返せる石があるかチェック
        rev = self._get_flippable(pos, color)
        
        # 1つも返せなければ置けない
        if rev == 0:
            return False
            
        # 3. 盤面更新 (排他的論理和ではなく、追加と削除を明確に行う)
        if color == Color.BLACK:
            self.black |= pos | rev  # 自分の石 + 返した石
            self.white &= ~rev       # 相手の石から返した分を削除
        else:
            self.white |= pos | rev
            self.black &= ~rev
        return True

    def _get_flippable(self, pos: int, color: Color) -> int:
        """指定した位置に石を置いた時に、反転する石のビットパターンを返す"""
        me = self.black if color == Color.BLACK else self.white
        opp = self.white if color == Color.BLACK else self.black
        
        rev = 0
        
        # 8方向への移動量 (座標系に合わせて修正済み)
        # 右(+1), 左(-1), 下(+8), 上(-8), ...
        directions = [1, -1, 8, -8, 7, -7, 9, -9]
        
        for d in directions:
            line_rev = 0
            tmp_pos = self._shift(pos, d)
            
            # 隣が相手の石である限り進む
            while (tmp_pos != 0) and (tmp_pos & opp):
                line_rev |= tmp_pos
                tmp_pos = self._shift(tmp_pos, d)
            
            # 最後に自分の石に到達していれば、そのラインは反転対象
            if (tmp_pos != 0) and (tmp_pos & me):
                rev |= line_rev
                
        return rev

    def _shift(self, b: int, shift: int) -> int:
        """
        ビットボードをシフトする。盤面の端(A列/H列)の回り込みを防止する。
        座標系: 左上(0,0)がLSB。右(+1)は左シフト(<<)、左(-1)は右シフト(>>)となる。
        """
        # マスク定義
        # H列(右端)を除くマスク: 0x7f7f... (01111111...)
        MASK_NOT_H = 0x7f7f7f7f7f7f7f7f
        # A列(左端)を除くマスク: 0xfefefe... (11111110...)
        MASK_NOT_A = 0xfefefefefefefefe
        
        if shift == 1:   return (b & MASK_NOT_H) << 1   # 右
        if shift == -1:  return (b & MASK_NOT_A) >> 1   # 左
        if shift == 8:   return (b << 8) & 0xffffffffffffffff # 下
        if shift == -8:  return (b >> 8)                # 上
        
        if shift == 9:   return (b & MASK_NOT_H) << 9   # 右下
        if shift == -9:  return (b & MASK_NOT_A) >> 9   # 左上
        if shift == 7:   return (b & MASK_NOT_A) << 7   # 左下 (左+1, 下+8 = +7 は間違い。左は-1なので 8-1=7) -> 実は 左下は +7
        # 検証: index 8 (1,0) -> 左下 (0,1) index 1.  8 -> 1 は -7 ?
        # 座標: (x, y). index = y*8 + x
        # 右下 (+1, +1) -> +9
        # 左上 (-1, -1) -> -9
        # 左下 (-1, +1) -> -1 + 8 = +7
        # 右上 (+1, -1) -> +1 - 8 = -7
        
        # なので：
        # +7 (左下): 左(-1)を含むので A列マスク & 左シフト
        if shift == 7:   return (b & MASK_NOT_A) << 7
        # -7 (右上): 右(+1)を含むので H列マスク & 右シフト
        if shift == -7:  return (b & MASK_NOT_H) >> 7
        
        return 0

    def get_legal_moves_bits(self, attacker_color: Color) -> int:
        """高速に合法手を生成する (Kogge-Stone Algorithm based)"""
        me = self.black if attacker_color == Color.BLACK else self.white
        opp = self.white if attacker_color == Color.BLACK else self.black
        
        # 空きマス (相手も自分もいない場所)
        blank = ~(self.black | self.white) & 0xffffffffffffffff

        # 左右端のマスク
        mask_h = 0x7e7e7e7e7e7e7e7e # 両端を除く

        legal = 0

        # 8方向のシフト量と、使用するマスク
        # shift > 0 なら << (左シフト), shift < 0 なら >> (右シフト)
        # 注意: _shiftメソッドとは異なり、ここではビット演算で一気に計算するため
        # 「右(+1)に行くには << 1」というロジックを直接書く。
        
        # (シフト量, 端のチェックが必要なマスク)
        # 左右 (+1, -1): 両端ガード
        # 上下 (+8, -8): 上下はビットあふれ/0埋めで自然に消えるのでマスク不要だが、oppとのANDは必須
        # 斜め (+7, -7, +9, -9): 両端ガード
        
        shifts_and_masks = [
            (1,  mask_h), (-1, mask_h), 
            (8,  opp),    (-8, opp),    # 上下は mask_h ではなく opp そのまま(左右関係ないため)
            (7,  mask_h), (-7, mask_h), 
            (9,  mask_h), (-9, mask_h)
        ]

        # ※ 上下(8, -8)の場合、mask_h(左右端除外)を使ってしまうと、端の列で縦に取れなくなるバグがあったため修正。
        # 正しくは「水平移動を含む方向（1, -1, 7, -7, 9, -9）」のみ mask_h を適用する。
        # しかし実装を単純にするため、以下のように分ける。

        # 1. 水平を含む方向 (左右、斜め) -> mask_h (0x7e...) と opp の AND をとる
        #    これで「端をまたぐ」のを防ぐ
        opp_masked_h = opp & 0x7e7e7e7e7e7e7e7e
        
        dirs = [
            (1, opp_masked_h), (-1, opp_masked_h), # 右, 左
            (8, opp), (-8, opp),                   # 下, 上 (左右端もOK)
            (7, opp_masked_h), (-7, opp_masked_h), # 左下, 右上
            (9, opp_masked_h), (-9, opp_masked_h)  # 右下, 左上
        ]

        for shift, mask in dirs:
            if shift > 0:
                # 正方向 (<<)
                t = (me << shift) & mask
                for _ in range(5): t |= (t << shift) & mask
                legal |= (t << shift) & blank
            else:
                # 負方向 (>>)
                s = -shift # シフト量を正にする
                t = (me >> s) & mask
                for _ in range(5): t |= (t >> s) & mask
                legal |= (t >> s) & blank

        return legal

    def display(self):
        print("  0 1 2 3 4 5 6 7")
        for y in range(8):
            row = []
            for x in range(8):
                pos = 1 << (y * 8 + x)
                if self.black & pos: row.append("○")
                elif self.white & pos: row.append("●")
                else: row.append("・")
            print(f"{y} " + " ".join(row))

    def count_stones(self) -> Tuple[int, int]:
        return bin(self.black).count('1'), bin(self.white).count('1')