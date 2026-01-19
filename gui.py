import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

# 既存のモジュールをインポート
from modules.game import Game
from modules.ai import RandomAI, MonteCarloAI, YosumiAI
from othello_rust import Color, BitboardOthello

# 利用可能なAIを登録
AI_CLASSES = {
    "Random AI": RandomAI,
    "Monte Carlo AI": MonteCarloAI,
    "Yosumi": YosumiAI
}

class OthelloGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rust Othello AI Battle")
        self.root.geometry("450x650")
        self.root.configure(bg="#f0f0f0")

        self.cell_size = 50
        self.is_running = False
        
        self.setup_ui()

    def setup_ui(self):
        # --- 設定エリア ---
        config_frame = ttk.LabelFrame(self.root, text="対戦設定", padding=10)
        config_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(config_frame, text="黒 (先手):").grid(row=0, column=0, sticky="w")
        self.black_ai_var = tk.StringVar(value="Random AI")
        self.black_combo = ttk.Combobox(config_frame, textvariable=self.black_ai_var, values=list(AI_CLASSES.keys()), state="readonly")
        self.black_combo.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(config_frame, text="白 (後手):").grid(row=1, column=0, sticky="w")
        self.white_ai_var = tk.StringVar(value="Monte Carlo AI")
        self.white_combo = ttk.Combobox(config_frame, textvariable=self.white_ai_var, values=list(AI_CLASSES.keys()), state="readonly")
        self.white_combo.grid(row=1, column=1, padx=5, pady=2)

        self.start_btn = ttk.Button(config_frame, text="対局開始", command=self.on_start_click)
        self.start_btn.grid(row=2, column=0, columnspan=2, pady=10)

        # --- 盤面エリア ---
        self.canvas = tk.Canvas(self.root, width=400, height=400, bg="#2e7d32", highlightthickness=2, highlightbackground="#333")
        self.canvas.pack(pady=10)
        self.draw_grid()

        # --- ステータスエリア ---
        self.status_label = ttk.Label(self.root, text="AIを選択してください", font=("Helvetica", 11))
        self.status_label.pack(pady=5)

        self.score_label = ttk.Label(self.root, text="黒: 2 | 白: 2", font=("Helvetica", 14, "bold"))
        self.score_label.pack(pady=5)

    def draw_grid(self):
        """8x8のマス目を描画"""
        for i in range(9):
            # 縦線・横線
            pos = i * self.cell_size
            self.canvas.create_line(pos, 0, pos, 400, fill="#1b5e20")
            self.canvas.create_line(0, pos, 400, pos, fill="#1b5e20")

    def draw_board(self, othello: BitboardOthello):
        """Rustのビットボードから石を描画"""
        self.canvas.delete("piece")
        
        # 修正箇所: get_black() ではなく プロパティ black / white にアクセス
        black_bits = othello.black
        white_bits = othello.white

        for i in range(64):
            # ビットボードのインデックスiから座標(x, y)を計算
            # Rust側: y * 8 + x なので、x = i % 8, y = i // 8
            x = i % 8
            y = i // 8
            mask = 1 << i
            
            color = None
            if black_bits & mask:
                color = "black"
            elif white_bits & mask:
                color = "white"
            
            if color:
                padding = 6
                x0, y0 = x * self.cell_size + padding, y * self.cell_size + padding
                x1, y1 = (x + 1) * self.cell_size - padding, (y + 1) * self.cell_size - padding
                self.canvas.create_oval(x0, y0, x1, y1, fill=color, outline="#333", tags="piece")
        
        # スコア更新
        b, w = othello.count_stones()
        self.score_label.config(text=f"黒: {b} | 白: {w}")

    def on_start_click(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.start_btn.config(state="disabled")
        
        # 別スレッドで対局ループを実行
        thread = threading.Thread(target=self.run_game_loop)
        thread.daemon = True
        thread.start()

    def run_game_loop(self):
        """Game.play()のロジックをGUI用に展開して実行"""
        BlackAI = AI_CLASSES[self.black_ai_var.get()]
        WhiteAI = AI_CLASSES[self.white_ai_var.get()]
        
        # Gameインスタンス生成
        game_manager = Game(BlackAI, WhiteAI)
        turn_color = Color.BLACK
        pass_count = 0

        # 初回描画
        self.root.after(0, self.draw_board, game_manager.othello)

        while pass_count < 2:
            current_ai = game_manager.black_ai if turn_color == Color.BLACK else game_manager.white_ai
            
            # ステータス更新
            color_name = "黒" if turn_color == Color.BLACK else "白"
            self.root.after(0, lambda c=color_name: self.status_label.config(text=f"{c} の思考中..."))
            
            # AIが着手決定
            move = current_ai.place()
            
            if move:
                x, y = move
                game_manager.othello.make_move(x, y, turn_color)
                pass_count = 0
            else:
                pass_count += 1
            
            # 描画更新と待機
            self.root.after(0, self.draw_board, game_manager.othello)
            time.sleep(0.1) # 観戦しやすいようにウェイトを入れる
            
            turn_color = Color.WHITE if turn_color == Color.BLACK else Color.BLACK

        # 終了処理
        winner = game_manager.winner()
        self.root.after(0, self.show_end_game, winner)

    def show_end_game(self, winner):
        self.is_running = False
        self.start_btn.config(state="normal")
        
        if winner == Color.BLACK:
            msg = "黒 (BLACK) の勝利！"
        elif winner == Color.WHITE:
            msg = "白 (WHITE) の勝利！"
        else:
            msg = "引き分けです"
            
        self.status_label.config(text="対局終了")
        messagebox.showinfo("Result", msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = OthelloGUI(root)
    root.mainloop()