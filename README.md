# APIM による LLM のマルチリージョン負荷分散・フェイルオーバー

Azure API Management（APIM）の組み込みバックエンドプール機能で、複数リージョンの Microsoft Foundry エンドポイントにデプロイした同一モデルへ、優先度（priority）と重み（weight）で推論リクエストをルーティングする構成の検証

優先度の高いバックエンドがレート制限に達すると、サーキットブレーカーと `retry` ポリシーにより下位優先度へ透過的にフェイルオーバーする。

元ネタは [AI-Gateway リポジトリの backend-pool-load-balancing ラボ](https://github.com/Azure-Samples/AI-Gateway/tree/main/labs/backend-pool-load-balancing)。

## ファイル

| ファイル | 役割 |
| --- | --- |
| `main.bicep` / `params.json` | インフラ定義とパラメータ |
| `policy.xml` | APIM の API ポリシー（バックエンドプール指定・リトライ） |
| `deploy.sh` / `cleanup.sh` | デプロイ・クリーンアップ |
| `01-load-balancing.py` | 負荷生成と応答リージョンの収集 |
| `02-plot.py` | 結果のグラフ化 |
| `requirements.txt` | Python の依存パッケージ |

## 構成

- APIM（Basicv2、システム割り当てマネージド ID）
- 4 リージョンの Microsoft Foundry アカウントと各アカウントへの `gpt-4.1-mini` デプロイ
  - foundry1: Japan East（優先度 1）
  - foundry2: Sweden Central（優先度 2 / 重み 50）
  - foundry3: East US 2（優先度 2 / 重み 50）
  - foundry4: UK South（優先度 3）
- APIM 上の Inference API・バックエンドプール（`inference-backend-pool`）・各バックエンドのサーキットブレーカー
- 各 Foundry への `Cognitive Services OpenAI User` ロール割り当て

## 前提

- Azure CLI（`az`）でログイン済み、対象サブスクリプションを選択済み
- 各リージョンに `gpt-4.1-mini`（GlobalStandard）のクォータ
- [uv](https://docs.astral.sh/uv/)（Python 実行）

## デプロイ

`deploy.sh` を実行すると、次の手順が自動で進む。再実行可能。

1. デプロイされるリソースの差分を事前表示（`az deployment group what-if`）
2. Bicep （`main.bicep` + `params.json`）をデプロイ
3. ゲートウェイ URL とサブスクリプションキーを `.env` に書き出し（検証コードが読み込む）

```bash
./deploy.sh
```

リージョン・優先度・重み・モデル・容量などのパラメータは [params.json](./params.json) で定義する。

## 検証の実行

`uv` が [requirements.txt](./requirements.txt) の依存を解決して実行する。事前のインストールは不要。

```bash
# APIM 経由で繰り返しリクエストする
uv run --with-requirements requirements.txt 01-load-balancing.py

# 結果を棒グラフ画像に保存する
uv run --with-requirements requirements.txt 02-plot.py
```

実行パラメータは環境変数で上書きできる。

| 変数 | 既定値 | 説明 |
| --- | --- | --- |
| `MODEL_NAME` | `gpt-4.1-mini` | デプロイ名 |
| `RUNS` | `30` | リクエスト回数 |
| `MAX_TOKENS` | `50` | 1 リクエストの出力上限 |
| `SLEEP_TIME_MS` | `100` | リクエスト間隔（ミリ秒） |

## クリーンアップ

リソースグループの削除に加え、ソフトデリート対象のパージまで行う。

```bash
./cleanup.sh
```
