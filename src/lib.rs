use pyo3::prelude::*;

// マスク定義
const MASK_NOT_A: u64 = 0xfefefefefefefefe; // 左端列(A列)以外
const MASK_NOT_H: u64 = 0x7f7f7f7f7f7f7f7f; // 右端列(H列)以外

#[pyclass]
#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Color {
    BLACK = 0,
    WHITE = 1,
}

#[pymethods]
impl Color {
    #[getter]
    fn other(&self) -> Color {
        match self {
            Color::BLACK => Color::WHITE,
            Color::WHITE => Color::BLACK,
        }
    }

    fn __repr__(&self) -> &str {
        match self {
            Color::BLACK => "Color.BLACK",
            Color::WHITE => "Color.WHITE",
        }
    }
}

#[pyclass]
#[derive(Clone, Copy)]
struct BitboardOthello {
    black: u64,
    white: u64,
}

#[pymethods]
impl BitboardOthello {
    #[new]
    fn new() -> Self {
        BitboardOthello {
            white: 0x0000001008000000,
            black: 0x0000000810000000,
        }
    }

    #[getter]
    fn get_black(&self) -> u64 { self.black }
    #[getter]
    fn get_white(&self) -> u64 { self.white }

    fn make_move(&mut self, x: i32, y: i32, color: Color) -> bool {
        if !(0..8).contains(&x) || !(0..8).contains(&y) {
            return false;
        }
        let pos: u64 = 1 << (y * 8 + x);
        if ((self.black | self.white) & pos) != 0 {
            return false;
        }

        let rev = self.get_flippable(pos, color);
        if rev == 0 {
            return false;
        }

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

    fn count_stones(&self) -> (u32, u32) {
        (self.black.count_ones(), self.white.count_ones())
    }

    fn get_legal_moves_bits(&self, color: Color) -> u64 {
        let (me, opp) = match color {
            Color::BLACK => (self.black, self.white),
            Color::WHITE => (self.white, self.black),
        };

        let blank = !(self.black | self.white);
        let mut legal = 0;

        let directions: [(i32, u64); 8] = [
            (1, MASK_NOT_A),  // 右
            (-1, MASK_NOT_H), // 左
            (8, 0xffffffffffffffff), // 下
            (-8, 0xffffffffffffffff), // 上
            (7, MASK_NOT_H),  // 左下
            (-7, MASK_NOT_A), // 右上
            (9, MASK_NOT_A),  // 右下
            (-9, MASK_NOT_H), // 左上
        ];

        for (d, mask) in directions {
            let mut t = self.shift_raw(me, d) & opp & mask;
            for _ in 0..5 {
                t |= self.shift_raw(t, d) & opp & mask;
            }
            legal |= self.shift_raw(t, d) & blank & mask;
        }
        legal
    }

    fn get_legal_moves(&self, color: Color) -> Vec<(i32, i32)> {
        let mut moves = Vec::new();
        let legal_bits = self.get_legal_moves_bits(color);
        for i in 0..64 {
            if (legal_bits >> i) & 1 == 1 {
                moves.push(((i % 8) as i32, (i / 8) as i32));
            }
        }
        moves
    }

    fn copy(&self) -> Self { *self }
    fn __copy__(&self) -> Self { *self }
}

impl BitboardOthello {
    fn get_flippable(&self, pos: u64, color: Color) -> u64 {
        let (me, opp) = match color {
            Color::BLACK => (self.black, self.white),
            Color::WHITE => (self.white, self.black),
        };

        let mut rev = 0;
        let directions: [i32; 8] = [1, -1, 8, -8, 7, -7, 9, -9];
        let masks: [u64; 8] = [
            MASK_NOT_A, MASK_NOT_H, 0xffffffffffffffff, 0xffffffffffffffff,
            MASK_NOT_H, MASK_NOT_A, MASK_NOT_A, MASK_NOT_H
        ];

        for i in 0..8 {
            let mut line_rev = 0;
            let mut tmp_pos = self.shift_raw(pos, directions[i]) & masks[i];
            while tmp_pos != 0 && (tmp_pos & opp) != 0 {
                line_rev |= tmp_pos;
                tmp_pos = self.shift_raw(tmp_pos, directions[i]) & masks[i];
            }
            if tmp_pos != 0 && (tmp_pos & me) != 0 {
                rev |= line_rev;
            }
        }
        rev
    }

    #[inline(always)]
    fn shift_raw(&self, b: u64, d: i32) -> u64 {
        if d > 0 { b << d } else { b >> (-d) }
    }
}

#[pymodule]
fn othello_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Color>()?;
    m.add_class::<BitboardOthello>()?;
    Ok(())
}