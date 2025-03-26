from flask import Flask, request, jsonify
import os
import sys
import json
import logging

# APIディレクトリをsys.pathに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# DataFunctionとPredictFunctionをインポート
from DataFunction import load_data
from PredictFunction import predict_admission

app = Flask(__name__)

@app.route('/api/DataFunction', methods=['GET'])
def data_function():
    try:
        # Azure Functionsと同様の形式でレスポンスを返す
        result = load_data.main(None)
        return jsonify(json.loads(result))
    except Exception as e:
        logging.error(f"データロードエラー: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/PredictFunction', methods=['POST'])
def predict_function():
    try:
        # リクエストデータを取得
        req_data = request.get_json()
        # Azure Functionsと同様の形式でレスポンスを返す
        result = predict_admission.main(req_data)
        return jsonify(json.loads(result))
    except Exception as e:
        logging.error(f"予測エラー: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return """
    <html>
    <head>
        <title>InHospital Forecast API</title>
        <meta http-equiv="refresh" content="0;url=/" />
    </head>
    <body>
        <p>APIサーバーが稼働中です。メインページにリダイレクトします。</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port) 