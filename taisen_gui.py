import sys
import threading
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QComboBox, QPushButton, QLabel, 
                             QGridLayout, QFrame, QMessageBox)
from PySide6.QtCore import Qt, Signal, QObject, QEventLoop
from PySide6.QtGui import QPainter, QColor

from othello_rust import Color, BitboardOthello

class GameSignals(QObject):
    update_board = Signal(object)
    update_status = Signal(str)
    update_score = Signal(int, int)
    game_over = Signal(object)
    human_moved = Signal(int, int) # 人間がクリックした座標(x, y)を送る

class OthelloBoard(QFrame):
    def __init__(self, signals, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 400)
        self.othello = None
        self.signals = signals
        self.human_turn = False # 人間が打てる状態かどうかのフラグ

    def update_data(self, othello):
        self.othello = othello
        self.update()

    def mousePressEvent(self, event):
        # 人間のターンでない、またはゲーム中以外は無視
        if not self.human_turn or self.othello is None:
            return

        # クリック座標から(x, y)を算出
        x = event.position().x() // 50
        y = event.position().y() // 50

        # 有効な手かどうか判定（Rust側のlegal_moves等を利用）
        # ※ make_moveができる場所かチェック
        if 0 <= x < 8 and 0 <= y < 8:
            self.signals.human_moved.emit(int(x), int(y))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#2e7d32"))
        painter.drawRect(0, 0, 400, 400)
        painter.setPen(QColor("#1b5e20"))
        for i in range(9):
            painter.drawLine(i * 50, 0, i * 50, 400)
            painter.drawLine(0, i * 50, 400, i * 50)

        if not self.othello: return
        black_bits, white_bits = self.othello.black, self.othello.white
        for i in range(64):
            x, y, mask = i % 8, i // 8, 1 << i
            rect = (x * 50 + 6, y * 50 + 6, 38, 38)
            if black_bits & mask:
                painter.setBrush(Qt.black)
                painter.drawEllipse(*rect)
            elif white_bits & mask:
                painter.setBrush(Qt.white)
                painter.drawEllipse(*rect)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rust Othello: Human vs AI")
        self.setFixedSize(450, 680)
        self.is_running = False
        self.signals = GameSignals()

        # UIを先に構築
        self.setup_ui()

        # シグナル接続
        self.signals.update_board.connect(self.board_widget.update_data)
        self.signals.update_status.connect(self.status_label.setText)
        self.signals.update_score.connect(self.update_score_label)
        self.signals.game_over.connect(self.show_end_game)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        config_group = QFrame()
        config_group.setFrameStyle(QFrame.StyledPanel)
        grid = QGridLayout(config_group)

        grid.addWidget(QLabel("あなた:"), 0, 0)
        grid.addWidget(QLabel("黒 (先手) 固定"), 0, 1)

        grid.addWidget(QLabel("対戦相手 (AI):"), 1, 0)
        self.ai_combo = QComboBox()
        # AI_CLASSESは既存のものを参照
        from modules.ai import RandomAI, MonteCarloAI, YosumiAI
        self.ai_map = {"Random": RandomAI, "Monte Carlo": MonteCarloAI, "Yosumi": YosumiAI}
        self.ai_combo.addItems(list(self.ai_map.keys()))
        grid.addWidget(self.ai_combo, 1, 1)

        self.start_btn = QPushButton("対局開始")
        self.start_btn.clicked.connect(self.start_game)
        grid.addWidget(self.start_btn, 2, 0, 1, 2)
        layout.addWidget(config_group)

        self.board_widget = OthelloBoard(self.signals)
        layout.addWidget(self.board_widget, alignment=Qt.AlignCenter)

        self.status_label = QLabel("対局を開始してください")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.score_label = QLabel("黒: 2 | 白: 2")
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.score_label)

    def update_score_label(self, b, w):
        self.score_label.setText(f"あなた(黒): {b} | AI(白): {w}")

    def start_game(self):
        if self.is_running: return
        self.is_running = True
        self.start_btn.setEnabled(False)
        threading.Thread(target=self.game_thread, daemon=True).start()

    def game_thread(self):
        # AIの準備
        AiClass = self.ai_map[self.ai_combo.currentText()]
        othello = BitboardOthello()
        ai_player = AiClass(Color.WHITE, othello)
        
        turn = Color.BLACK
        pass_count = 0

        while pass_count < 2:
            self.signals.update_board.emit(othello)
            b, w = othello.count_stones()
            self.signals.update_score.emit(b, w)

            # パス判定
            if not othello.get_legal_moves(turn):
                pass_count += 1
                turn = Color.WHITE if turn == Color.BLACK else Color.BLACK
                continue
            
            pass_count = 0
            if turn == Color.BLACK:
                # --- 人間のターン ---
                self.signals.update_status.emit("あなたの番です (黒)")
                self.board_widget.human_turn = True
                
                loop = QEventLoop()
                selected_move = []

                def handle_move(x, y):
                    # Rust側から [(x, y), (x, y), ...] 形式でリストが返ってくる
                    legal_moves = othello.get_legal_moves(Color.BLACK)
                    
                    # クリックした (x, y) がそのリストに含まれているか直接チェック
                    # ※ タプルかリストかの違いを吸収するため、tuple(move) で比較
                    current_click = (int(x), int(y))
                    
                    if current_click in [tuple(m) for m in legal_moves]:
                        selected_move.append((x, y))
                        loop.quit()
                    else:
                        self.signals.update_status.emit(f"({x}, {y}) は打てません。")

                self.signals.human_moved.connect(handle_move)
                loop.exec() 
                self.signals.human_moved.disconnect(handle_move)
                
                self.board_widget.human_turn = False
                mx, my = selected_move[0]
                othello.make_move(mx, my, Color.BLACK)
            else:
                # --- AIのターン ---
                self.signals.update_status.emit("AIが思考中です...")
                time.sleep(0.5) # 少し間を置く
                move = ai_player.place()
                if move:
                    othello.make_move(move[0], move[1], Color.WHITE)
            
            turn = Color.WHITE if turn == Color.BLACK else Color.BLACK

        self.signals.update_board.emit(othello)
        def winner():
            b, w = othello.count_stones()
            if b > w:
                return Color.BLACK
            elif w > b:
                return Color.WHITE
            else:
                return None
        self.signals.game_over.emit(winner())

    def show_end_game(self, winner):
        self.is_running = False
        self.start_btn.setEnabled(True)
        res = "あなたの勝利！" if winner == Color.BLACK else "AIの勝利！" if winner == Color.WHITE else "引き分け"
        QMessageBox.information(self, "終局", res)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())