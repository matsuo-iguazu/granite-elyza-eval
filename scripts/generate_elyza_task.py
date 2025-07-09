import os
import json
import argparse
import requests
from datasets import load_dataset
from tqdm import tqdm

# 定数定義
# Watsonx.ai APIのエンドポイントURL
URL = "https://jp-tok.ml.cloud.ibm.com/ml/v1/text/generation?version=2024-03-14"
# ELYZA-tasks-100データセットの名前と分割
DATASET_NAME = "elyza/ELYZA-tasks-100"
SPLIT = "test"


def load_tasks(n):
    """
    Hugging Face datasets から ELYZA-tasks-100 の先頭 n 件を読み込みます。
    必要なカラムが存在するかを検証します。
    """
    ds = load_dataset(DATASET_NAME, split=SPLIT)
    required = {"input", "output", "eval_aspect"}
    if not required.issubset(set(ds.column_names)):
        raise ValueError(f"必要なカラムがありません: {ds.column_names}")
    return ds.select(range(n))


def call_model(question, model_id, token, project_id):
    """
    Watsonx.aiに質問を送り、生成テキストを取得して返します。
    """
    # モデルに渡すプロンプトの形式
    prompt = (
        "### System:\n"
        "あなたは誠実で優秀なAIアシスタントです。ユーザーの指示に可能な限り正確に従ってください。"
        "日本語での指示には日本語のみで応答してください。\n"
        "### User:\n"
        f"{question}\n"
        "### Assistant:\n"
    )
    # APIリクエストのボディ
    body = {
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy", # デコーディング方法（貪欲法）
            "max_new_tokens": 4096,     # 生成する最大トークン数
            "min_new_tokens": 0,        # 生成する最小トークン数
            "repetition_penalty": 1.1   # 反復ペナルティ
        },
        "model_id": f"ibm/{model_id}", # 使用するモデルID
        "project_id": project_id       # プロジェクトID
    }
    # リクエストヘッダー
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}" # 認証トークン
    }

    # APIリクエストの実行
    response = requests.post(URL, headers=headers, json=body)
    if response.status_code != 200:
        print(f"Error: HTTP {response.status_code} - {response.text}")
        return None

    data = response.json()
    try:
        # 応答から生成されたテキストを抽出
        result = data.get("results", [])[0]
        text = result.get("generated_text", "").strip()
        # 不要な末尾のトークンを削除
        if text.endswith("</s>"):
            text = text[:-4]
    except Exception as e:
        print(f"Warning: Unexpected response format or error processing response: {e} - {data}")
        return None
    return text


def main():
    parser = argparse.ArgumentParser(description="Elyza-task-100 モデル比較スクリプト")
    parser.add_argument('-m', '--model', required=True,
                        choices=['granite-8b-japanese', 'granite-3-8b-instruct'],
                        help='使用する基盤モデル名')
    parser.add_argument('-n', '--number', type=int, default=100,
                        help='処理するタスク件数 (デフォルト: 100)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='質問と応答結果を表示する')
    args = parser.parse_args()

    # 環境変数からWATSONX_TOKENを読み込み
    token = os.getenv("WATSONX_TOKEN")
    if not token:
        print("環境変数 WATSONX_TOKEN が設定されていません。")
        return
    token = token.strip()

    # 環境変数からPROJECT_IDを読み込み
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        print("環境変数 PROJECT_ID が設定されていません。")
        return
    project_id = project_id.strip()

    tasks = load_tasks(args.number)
    print(f"Loaded {len(tasks)} tasks from dataset {DATASET_NAME} split={SPLIT}")

    # 出力ファイル名設定
    # モデルIDをファイル名に含め、特殊文字を置換
    sanitized_model_id = args.model.replace("/", "_").replace("-", "_")
    # ensure_ascii=True でASCIIエンコードされたファイル（評価用）
    encoded_file_path = os.path.join("data", "raw_model_responses", f"watsonx_{sanitized_model_id}_elyza100_encoded.jsonl")
    # ensure_ascii=False で可読性の高いファイル
    readable_file_path = os.path.join("data", "raw_model_responses", f"watsonx_{sanitized_model_id}_elyza100_readable.jsonl")

    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(encoded_file_path), exist_ok=True)

    with open(encoded_file_path, 'w', encoding='utf-8') as fe, \
         open(readable_file_path, 'w', encoding='utf-8') as fr:
        for idx, task in enumerate(tqdm(tasks, total=len(tasks), desc="Processing"), start=1):
            question = task['input']
            # モデル呼び出しにproject_idを追加
            model_answer = call_model(question, args.model, token, project_id)
            if model_answer is None:
                print(f"Skipping question {idx} due to error.")
                continue

            result = {
                'Question': question,
                'output': task['output'],
                'eval_aspect': task['eval_aspect'],
                'ModelAnswer': model_answer
            }
            # JSONL書き込み (ensure_ascii=True: 評価用, ensure_ascii=False: 可読用)
            fe.write(json.dumps(result, ensure_ascii=True) + "\n")
            fr.write(json.dumps(result, ensure_ascii=False) + "\n")

            if args.verbose:
                print(f"[{idx}/{len(tasks)}] Q: {question}")
                print(f"          A: {model_answer}\n")

    print(f"Completed. Output files:\n  {encoded_file_path}\n  {readable_file_path}")


if __name__ == '__main__':
    main()
