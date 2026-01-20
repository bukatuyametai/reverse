import sys
import threading
import time
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QComboBox, QPushButton, QLabel, 
                             QGridLayout, QFrame, QMessageBox)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QPainter, QColor, QFont

# 既存モジュールのインポート（パスが通っている前提）
from modules.game import Game
from modules.ai import RandomAI, MonteCarloAI, YosumiAI
from othello_rust import Color, BitboardOthello

AI_CLASSES = {
    "Random AI": RandomAI,
    "Monte Carlo AI": MonteCarloAI,
    "Yosumi": YosumiAI
}

# スレッド間でUI更新を安全に行うためのシグナル用クラス
class GameSignals(QObject):
    update_board = Signal(object)
    update_status = Signal(str)
    update_score = Signal(int, int)
    game_over = Signal(object)

class OthelloBoard(QFrame):
    """盤面描画専用のウィジェット"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 400)
        self.othello = None

    def update_data(self, othello):
        self.othello = othello
        self.update() # 再描画をトリガー

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 背景（緑）
        painter.setBrush(QColor("#2e7d32"))
        painter.drawRect(0, 0, 400, 400)

        # 罫線
        painter.setPen(QColor("#1b5e20"))
        cell_size = 50
        for i in range(9):
            painter.drawLine(i * cell_size, 0, i * cell_size, 400)
            painter.drawLine(0, i * cell_size, 400, i * cell_size)

        if not self.othello:
            return

        # 石の描画
        black_bits = self.othello.black
        white_bits = self.othello.white
        padding = 6

        for i in range(64):
            x = i % 8
            y = i // 8
            mask = 1 << i
            
            rect = (x * cell_size + padding, y * cell_size + padding, 
                    cell_size - padding*2, cell_size - padding*2)

            if black_bits & mask:
                painter.setBrush(Qt.black)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(*rect)
            elif white_bits & mask:
                painter.setBrush(Qt.white)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(*rect)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setWindowTitle("Rust Othello AI Battle")
        self.setFixedSize(450, 650)
        self.is_running = False

        self.signals = GameSignals()
        self.signals.update_board.connect(self.board_widget.update_data)
        self.signals.update_status.connect(self.status_label.setText)
        self.signals.update_score.connect(self.update_score_label)
        self.signals.game_over.connect(self.show_end_game)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # --- 設定エリア ---
        config_group = QFrame()
        config_group.setFrameStyle(QFrame.StyledPanel)
        config_layout = QGridLayout(config_group)

        config_layout.addWidget(QLabel("黒 (先手):"), 0, 0)
        self.black_combo = QComboBox()
        self.black_combo.addItems(list(AI_CLASSES.keys()))
        config_layout.addWidget(self.black_combo, 0, 1)

        config_layout.addWidget(QLabel("白 (後手):"), 1, 0)
        self.white_combo = QComboBox()
        self.white_combo.addItems(list(AI_CLASSES.keys()))
        self.white_combo.setCurrentText("Monte Carlo AI")
        config_layout.addWidget(self.white_combo, 1, 1)

        self.start_btn = QPushButton("対局開始")
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self.on_start_click)
        config_layout.addWidget(self.start_btn, 2, 0, 1, 2)

        layout.addWidget(config_group)

        # --- 盤面エリア ---
        self.board_widget = OthelloBoard()
        layout.addWidget(self.board_widget, alignment=Qt.AlignCenter)

        # --- ステータスエリア ---
        self.status_label = QLabel("AIを選択してください")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.score_label = QLabel("黒: 2 | 白: 2")
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.score_label)

    def update_score_label(self, b, w):
        self.score_label.setText(f"黒: {b} | 白: {w}")

    def on_start_click(self):
        if self.is_running: return
        self.is_running = True
        self.start_btn.setEnabled(False)
        
        thread = threading.Thread(target=self.run_game_loop)
        thread.daemon = True
        thread.start()

    def run_game_loop(self):
        BlackAI = AI_CLASSES[self.black_combo.currentText()]
        WhiteAI = AI_CLASSES[self.white_combo.currentText()]
        
        game_manager = Game(BlackAI, WhiteAI)
        turn_color = Color.BLACK
        pass_count = 0

        self.signals.update_board.emit(game_manager.othello)

        while pass_count < 2:
            current_ai = game_manager.black_ai if turn_color == Color.BLACK else game_manager.white_ai
            color_name = "黒" if turn_color == Color.BLACK else "白"
            self.signals.update_status.emit(f"{color_name} の思考中...")
            
            move = current_ai.place()
            if move:
                x, y = move
                game_manager.othello.make_move(x, y, turn_color)
                pass_count = 0
            else:
                pass_count += 1
            
            self.signals.update_board.emit(game_manager.othello)
            b, w = game_manager.othello.count_stones()
            self.signals.update_score.emit(b, w)
            
            time.sleep(0.1)
            turn_color = Color.WHITE if turn_color == Color.BLACK else Color.BLACK

        winner = game_manager.winner()
        self.signals.game_over.emit(winner)

    def show_end_game(self, winner):
        self.is_running = False
        self.start_btn.setEnabled(True)
        
        if winner == Color.BLACK: msg = "黒 (BLACK) の勝利！"
        elif winner == Color.WHITE: msg = "白 (WHITE) の勝利！"
        else: msg = "引き分けです"
            
        self.status_label.setText("対局終了")
        QMessageBox.information(self, "対局結果", msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 日本語が化ける場合は明示的にフォントを指定可能
    # app.setFont(QFont("Microsoft YaHei", 9)) 
    window = MainWindow()
    window.show()
    sys.exit(app.exec())