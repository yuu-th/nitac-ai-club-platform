import io
import sys

import kaggle_best_score


def main():
    # 標準出力を抑制
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        example.main()  # 実行したい関数を呼び出し
    finally:
        # 標準出力を元に戻す
        sys.stdout = original_stdout


if __name__ == "__main__":
    main()
