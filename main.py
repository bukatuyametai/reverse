import time
from game import Game
from ai import RandomAI, YosumiAI
from othello_rust import Color

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