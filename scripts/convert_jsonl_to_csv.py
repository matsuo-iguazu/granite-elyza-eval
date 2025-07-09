import json
import pandas as pd
import os
import argparse

def convert_jsonl_to_csv(input_jsonl_path, output_csv_path):
    """
    JSONLファイルを読み込み、Pandas DataFrameに変換し、CSVとして保存します。
    Shaberiの評価結果を可読性の高いCSVにするためのものです。
    """
    data = []
    try:
        with open(input_jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line.strip()))
    except FileNotFoundError:
        print(f"エラー: 入力ファイルが見つかりません - {input_jsonl_path}")
        return
    except json.JSONDecodeError as e:
        print(f"エラー: JSONLファイルの解析に失敗しました - {input_jsonl_path} ({e})")
        return

    if not data:
        print(f"警告: 入力ファイル {input_jsonl_path} にデータがありません。")
        return

    # DataFrameを作成
    df = pd.DataFrame(data)

    # 必要に応じて、CSVに含める列の順序を調整したり、不要な列を削除したりできます。
    # 例: df = df[['Question', 'output', 'ModelAnswer', 'score', 'reason']]
    # Shaberiの出力には 'score' や 'reason' (または 'JudgeScore', 'JudgeReason') が含まれるはずです。
    # ここでは例として、Shaberiの出力に含まれる可能性のある列名をコメントで示しています。
    # 実際のShaberiの出力JSONLを確認し、適切な列名を使用してください。
    # 例: df = df[['Question', 'output', 'ModelAnswer', 'score', 'reason']] # もしShaberiの出力がこれらを含む場合

    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)

    # CSVとして保存
    # Excelで開けるようにutf-8-sigエンコーディングを使用
    df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"JSONLファイルをCSVに変換しました: {output_csv_path}")


def main():
    parser = argparse.ArgumentParser(description="ShaberiのJSONL評価結果をCSVに変換するスクリプト")
    parser.add_argument('--model', required=True,
                        help='評価対象のモデル名 (例: granite-3-8b-instruct)')
    args = parser.parse_args()

    # モデルIDをファイル名に含め、特殊文字を置換
    sanitized_model_id = args.model.replace("/", "_").replace("-", "_")

    # 入力と出力のパスを設定
    # shaberiの出力ファイルパスと、あなたのリポジトリのCSV出力パスを結合
    input_jsonl_path = os.path.join("results", "shisa_judge_results",
                                    f"watsonx_{sanitized_model_id}_shisa_results.jsonl")
    output_csv_path = os.path.join("results", "readable_csv_results",
                                   f"watsonx_{sanitized_model_id}_elyza100_readable_results.csv")

    convert_jsonl_to_csv(input_jsonl_path, output_csv_path)

if __name__ == '__main__':
    main()
