# granite-elyza-eval

本リポジトリは、[あなたのブログ記事タイトル] で解説されている、IBM watsonx.ai の Granite モデルの日本語応答性能評価に関するコードとデータを提供します。

詳細な分析、評価の背景、および結果の考察については、以下のブログ記事をご覧ください。
[▶️ ブログ記事はこちら](ブログ記事のURL)

---

## 📂 リポジトリ構成

* `scripts/`: モデル応答生成スクリプトおよび結果変換スクリプト
* `data/`: ELYZA-tasks-100データセットとモデルの生応答データ
* `results/`: Shaberiによる評価結果（JSONL）と、可読性を高めたCSV形式の結果

---

## 🚀 作業手順

このリポジトリのコードを実行し、評価結果を生成するための手順です。

### 1. 環境準備

1.  **リポジトリのクローン**:
    ```bash
    git clone https://github.com/your-username/granite-elyza-eval.git
    cd granite-elyza-eval
    ```
2.  **Shaberiリポジトリのクローン**:
    ```bash
    # /workspaces のような親ディレクトリに移動してからクローン
    cd /workspaces
    git clone https://github.com/shisa-ai/shaberi.git
    ```
3.  **Python仮想環境の作成とアクティベート**:
    ```bash
    cd /workspaces/granite-elyza-eval # あなたのリポジトリに戻る
    python -m venv .venv
    source .venv/bin/activate
    ```
4.  **必要なライブラリのインストール**:
    ```bash
    pip install -r requirements.txt
    # Shaberiの依存関係もインストール
    pip install -r ../shaberi/requirements.txt
    ```
5.  **環境変数の設定**:
    * `WATSONX_API_KEY` (IBM Cloud APIキー)
    * `PROJECT_ID` (watsonx.ai watsonx.ai StudioプロジェクトID)
    * `OPENAI_API_KEY` (Shaberiの評価用LLM用)

    ```bash
    export WATSONX_API_KEY="YOUR_IBM_CLOUD_API_KEY"
    export PROJECT_ID="YOUR_WATSONX_PROJECT_ID"
    export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
    ```
    * `WATSONX_TOKEN` は `WATSONX_API_KEY` から以下のコマンドで生成します（時限トークン）。
        ```bash
        export WATSONX_TOKEN=$(curl -X POST \
          "https://iam.cloud.ibm.com/identity/token" \
          -H 'Content-Type: application/x-www-form-urlencoded' \
          -H 'Accept: application/json' \
          --data-urlencode "grant_type=urn:ibm:params:oauth:grant-type:apikey" \
          --data-urlencode "apikey=${WATSONX_API_KEY}" | jq -r '.access_token')
        ```

### 2. モデル応答の生成

`scripts/generate_elyza_task.py` を実行し、Watsonx.ai のモデルから ELYZA-tasks-100 への応答を生成します。-mオプションはgranite-3-8b-instructかgranite-8b-japaneseを使います。

```bash
python scripts/generate_elyza_task.py -m granite-3-8b-instruct -n 100 # または -n で件数指定
```
* 生成されたファイル（評価用）: `data/raw_model_responses/watsonx_granite_3_8b_instruct_elyza100_encoded.jsonl` など
* 生成されたファイル（確認用）: `data/raw_model_responses/watsonx_granite_3_8b_instruct_elyza100_readable.jsonl` など

### 3. Shaberiによる評価

生成したモデル応答をShaberiが評価できるように配置し、`judge_answers.py` を実行します。コマンド中のモデル文字列はgranite-3-8b-instructかgranite-8b-japaneseを使います。

1.  **モデル応答ファイルをShaberiの指定場所にコピー**:
    ```bash
    # mkdir -p /workspaces/shaberi/data/model_answers/elyza__ELYZA-tasks-100
    cp -p data/raw_model_responses/watsonx_granite_3_8b_instruct_elyza100_encoded.jsonl \
        /workspaces/shaberi/data/model_answers/elyza__ELYZA-tasks-100/ibm__granite-3-8b-instruct.json
    ```
2.  **Shaberiの評価スクリプトを実行**:
    ```bash
    cd /workspaces/shaberi/ # Shaberiリポジトリに移動
    python judge_answers.py \
      -m "ibm/granite-3-8b-instruct" \
      -d "elyza/ELYZA-tasks-100"
    ```
* 生成されたファイル: `/workspaces/shaberi/data/judgements/judge_gpt-4.1-2025-04-14/elyza__ELYZA-tasks-100/ibm__granite-3-8b-instruct.json` など

### 4. 評価結果の整理

Shaberiの評価結果をあなたのリポジトリにコピーし、可読性の高いCSV形式に変換します。

1.  **Shaberiの評価結果をあなたのリポジトリにコピー**:
    ```bash
    cd /workspaces/granite-elyza-eval # あなたのリポジトリに戻る
    mkdir -p results/shisa_judge_results
    cp -p /workspaces/shaberi/data/judgements/judge_gpt-4.1-2025-04-14/elyza__ELYZA-tasks-100/ibm__granite-3-8b-instruct.json \
        results/shisa_judge_results/watsonx_granite_3_8b_instruct_shisa_results.jsonl
    ```
2.  **CSV変換スクリプトを実行**:
    ```bash
    python scripts/convert_jsonl_to_csv.py --model granite-3-8b-instruct
    ```
* 生成されたファイル: `results/readable_csv_results/watsonx_granite_3_8b_instruct_elyza100_readable_results.csv` など

---

## 📊 最終結果データ

最終的な評価結果（CSV形式）は `results/readable_csv_results/watsonx_granite_3_8b_instruct_elyza100_readable_results.csv` などでご確認いただけます。

モデルの生応答データは `data/raw_model_responses/` に、Shaberiによる詳細なJSONL結果は `results/shisa_judge_results/` にそれぞれ保存されています。

---

## 📝 ライセンス

本リポジリのコンテンツは [MIT License](LICENSE) の下で公開されています。
