import logging
import azure.functions as func
import json
from ..SharedCode.storage import AzureStorageManager

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('予測API関数が呼び出されました')

    try:
        # リクエストボディからデータを取得
        req_body = req.get_json()
        logging.info(f"リクエストデータ: {req_body}")

        # ストレージマネージャーを初期化
        storage_manager = AzureStorageManager()
        
        # モデルを読み込む
        model = storage_manager.load_model('fixed_rf_model.joblib')
        if model is None:
            return func.HttpResponse(
                json.dumps({"error": "モデルの読み込みに失敗しました"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # 入力データの前処理
        import pandas as pd
        input_df = pd.DataFrame([req_body])
        
        # 予測を実行
        prediction = model.predict(input_df)[0]
        logging.info(f"予測結果: {prediction}")
        
        # レスポンスを返す
        return func.HttpResponse(
            json.dumps({"prediction": float(prediction)}),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"予測処理エラー: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        ) 