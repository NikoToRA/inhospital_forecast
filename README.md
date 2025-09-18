# 入院患者数予測システム

病院の入院患者数を予測するシステムのフロントエンドとバックエンドを含んだWebアプリケーションです。
RandomForestモデルを使用して、翌日の入院患者数を予測します。

## 機能

- 病院データ（曜日、祝日フラグ、外来患者数など）から翌日の入院患者数を予測
- モダンなUIによる入力フォームと予測結果の表示
- 様々なシナリオの自動予測機能
- データ分析ダッシュボード
- Supabaseとの連携によるデータ管理

## 技術スタック

### バックエンド
- Python 3.8+
- Flask (Webフレームワーク)
- scikit-learn (機械学習)
- pandas (データ処理)
- Supabase (データベース)

### フロントエンド
- React 18
- Material-UI
- Chart.js
- Axios (HTTP通信)

### インフラ
- Render (デプロイメント)
- Supabase (データベース)

## ローカル環境での実行方法

### 前提条件
- Python 3.8以上
- Node.js 16以上
- pip
- npm

### バックエンドのセットアップ
```bash
# リポジトリをクローン
git clone https://github.com/yourusername/inhospital_forecast.git
cd inhospital_forecast

# Pythonの仮想環境を作成（オプション）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# バックエンドの依存関係をインストール
cd backend
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envファイルを編集して、Supabaseの認証情報を設定

# バックエンドサーバーを起動
python app.py
```

### フロントエンドのセットアップ
```bash
# 別のターミナルで
cd frontend

# 依存関係をインストール
npm install

# 開発サーバーを起動
npm start
```

ブラウザで http://localhost:3000 を開くと、アプリケーションにアクセスできます。

## Renderへのデプロイ

### 手動デプロイ
1. Renderのアカウントを作成し、新しいWebサービスを作成
2. リポジトリを接続
3. 以下の環境変数を設定：
   - `SUPABASE_URL`: SupabaseプロジェクトのURL
   - `SUPABASE_KEY`: Supabaseの匿名キー
   - `FLASK_ENV`: production
   - `MODEL_PATH`: fixed_rf_model.joblib

### 自動デプロイ
1. リポジトリに含まれる `render.yaml` を使用
2. Renderのダッシュボードで環境変数を設定
3. デプロイを開始

## Supabaseのセットアップ

1. Supabaseで新しいプロジェクトを作成
2. データベースのテーブルを作成
3. 認証情報を取得し、環境変数に設定

## ライセンス

MIT

## 作者

Your Name 