use pyo3::prelude::*;

// マスク定義
const MASK_NOT_H: u64 = 0x7f7f7f7f7f7f7f7f;
const MASK_NOT_A: u64 = 0xfefefefefefefefe;
const FULL_MASK: u64 = 0xffffffffffffffff;

#[pyclass]
#[derive(Clone, Copy, PartialEq)]
enum Color {
    BLACK = 0,
    WHITE = 1,
}

#[pyclass]
struct BitboardOthello {
    black: u64,
    white: u64,
}

#[pymethods]
impl BitboardOthello {
    #[new]
    fn new() -> Self {
        // 初期配置
        // 白: (3,3) -> 27, (4,4) -> 36
        // 黒: (4,3) -> 28, (3,4) -> 35
        BitboardOthello {
            white: 0x0000001008000000,
            black: 0x0000000810000000,
        }
    }

    /// 黒のビットボードを取得 (デバッグ/可視化用)
    #[getter]
    fn get_black(&self) -> u64 { self.black }
    
    /// 白のビットボードを取得
    #[getter]
    fn get_white(&self) -> u64 { self.white }

    /// 指定した位置に石を置く
    fn make_move(&mut self, x: i32, y: i32, color: Color) -> bool {
        if !(0..8).contains(&x) || !(0..8).contains(&y) {
            return false;
        }

        let pos: u64 = 1 << (y * 8 + x);

        // 1. 既に石があるか
        if ((self.black | self.white) & pos) != 0 {
            return false;
        }

        // 2. ひっくり返せるか
        let rev = self.get_flippable(pos, color);
        if rev == 0 {
            return false;
        }

        // 3. 盤面更新
        match color {
            Color::BLACK => {
                self.black |= pos | rev;
                self.white &= !rev;
            }
            Color::WHITE => {
                self.white |= pos | rev;
                self.black &= !rev;
            }
        }
        true
    }

    /// 石の数を数える (黒, 白)
    fn count_stones(&self) -> (u32, u32) {
        (self.black.count_ones(), self.white.count_ones())
    }

    /// 高速に合法手を生成する (Kogge-Stone Algorithm)
    fn get_legal_moves_bits(&self, attacker_color: Color) -> u64 {
        let (me, opp) = match attacker_color {
            Color::BLACK => (self.black, self.white),
            Color::WHITE => (self.white, self.black),
        };

        let blank = !(self.black | self.white);
        let opp_masked_h = opp & 0x7e7e7e7e7e7e7e7e; // 水平方向用マスク済み相手石
        
        let mut legal = 0;

        // 8方向の定義: (シフト量, マスク)
        // シフト量: 正=左シフト(<<), 負=右シフト(>>)
        // Pythonコードのlogicに対応: 
        // 左右(+1,-1), 斜め(+7,-7,+9,-9) -> opp_masked_h
        // 上下(+8,-8) -> opp (そのまま)
        
        let dirs = [
            (1, opp_masked_h), (-1, opp_masked_h), // 右, 左
            (8, opp),          (-8, opp),          // 下, 上
            (7, opp_masked_h), (-7, opp_masked_h), // 左下, 右上
            (9, opp_masked_h), (-9, opp_masked_h)  // 右下, 左上
        ];

        for (shift, mask) in dirs.iter() {
            let mut t: u64;
            if *shift > 0 {
                let s = *shift as u32; // u32 for shift op
                t = (me << s) & mask;
                for _ in 0..5 {
                    t |= (t << s) & mask;
                }
                legal |= (t << s) & blank;
            } else {
                let s = (-shift) as u32; // abs(shift)
                t = (me >> s) & mask;
                for _ in 0..5 {
                    t |= (t >> s) & mask;
                }
                legal |= (t >> s) & blank;
            }
        }

        legal
    }
}

// 内部ヘルパー関数 (Pythonには公開しない)
impl BitboardOthello {
    fn get_flippable(&self, pos: u64, color: Color) -> u64 {
        let (me, opp) = match color {
            Color::BLACK => (self.black, self.white),
            Color::WHITE => (self.white, self.black),
        };

        let mut rev = 0;
        // 8方向のシフト量
        let directions = [1, -1, 8, -8, 7, -7, 9, -9];

        for &d in directions.iter() {
            let mut line_rev = 0;
            let mut tmp_pos = Self::shift(pos, d);

            while tmp_pos != 0 && (tmp_pos & opp) != 0 {
                line_rev |= tmp_pos;
                tmp_pos = Self::shift(tmp_pos, d);
            }

            if tmp_pos != 0 && (tmp_pos & me) != 0 {
                rev |= line_rev;
            }
        }
        rev
    }

    #[inline(always)]
    fn shift(b: u64, shift: i32) -> u64 {
        match shift {
            1 => (b & MASK_NOT_H) << 1,   // 右
            -1 => (b & MASK_NOT_A) >> 1,  // 左
            8 => (b << 8),                // 下 (オーバーフローは自動破棄)
            -8 => (b >> 8),               // 上
            9 => (b & MASK_NOT_H) << 9,   // 右下
            -9 => (b & MASK_NOT_A) >> 9,  // 左上
            7 => (b & MASK_NOT_A) << 7,   // 左下
            -7 => (b & MASK_NOT_H) >> 7,  // 右上
            _ => 0,
        }
    }
}

/// モジュールの登録
#[pymodule]
fn othello_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Color>()?;
    m.add_class::<BitboardOthello>()?;
    Ok(())
}