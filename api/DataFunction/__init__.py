import logging
import azure.functions as func
import json
import pandas as pd
from datetime import datetime
from ..SharedCode.storage import AzureStorageManager

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('データAPI関数が呼び出されました')
    
    # リクエストメソッドの確認
    if req.method == "GET":
        return load_data_handler(req)
    elif req.method == "POST":
        return save_data_handler(req)
    else:
        return func.HttpResponse(
            json.dumps({"error": "サポートされていないHTTPメソッドです"}),
            status_code=405,
            mimetype="application/json"
        )

def load_data_handler(req: func.HttpRequest) -> func.HttpResponse:
    """データ読み込みハンドラー"""
    logging.info('データ読み込みAPIが呼び出されました')
    
    try:
        # ストレージマネージャを初期化
        storage_manager = AzureStorageManager()
        
        # CSVデータの読み込み
        df = storage_manager.load_data('ultimate_pickup_data.csv')
        if df is None:
            return func.HttpResponse(
                json.dumps({"error": "データの読み込みに失敗しました"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # データをJSON形式に変換
        data_json = df.to_dict(orient='records')
        
        # レスポンスを返す
        return func.HttpResponse(
            json.dumps({"data": data_json}),
            status_code=200,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"データ読み込みエラー: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"データ読み込みエラー: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

def save_data_handler(req: func.HttpRequest) -> func.HttpResponse:
    """データ保存ハンドラー"""
    logging.info('データ保存APIが呼び出されました')
    
    try:
        # リクエストボディからデータを取得
        req_body = req.get_json()
        logging.info(f"保存データ: {req_body}")
        
        # データを抽出
        date = req_body.get('date')
        day_data = req_body.get('day_data')
        input_data = req_body.get('input_data')
        real_admission = req_body.get('real_admission')
        
        # 入力検証
        if not all([date, day_data, input_data, real_admission]):
            return func.HttpResponse(
                json.dumps({"error": "必須パラメータが不足しています"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # ストレージマネージャを初期化
        storage_manager = AzureStorageManager()
        
        # 既存のデータを読み込む
        df = storage_manager.load_data('ultimate_pickup_data.csv')
        if df is None:
            # ファイルが存在しない場合は新規作成
            df = pd.DataFrame(columns=['date', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 
                                       'public_holiday', 'public_holiday_previous_day', 
                                       'total_outpatient', 'intro_outpatient', 'ER', 'bed_count', 'y'])
        
        # 日付が既に存在するかチェック
        if date in df['date'].values:
            # 既存のデータを削除
            df = df[df['date'] != date]
        
        # 新しいデータを作成
        new_data = {
            'date': date,
            'mon': day_data['mon'],
            'tue': day_data['tue'],
            'wed': day_data['wed'],
            'thu': day_data['thu'],
            'fri': day_data['fri'],
            'sat': day_data['sat'],
            'sun': day_data['sun'],
            'public_holiday': input_data['public_holiday'],
            'public_holiday_previous_day': input_data['public_holiday_previous_day'],
            'total_outpatient': input_data['total_outpatient'],
            'intro_outpatient': input_data['intro_outpatient'],
            'ER': input_data['ER'],
            'bed_count': input_data['bed_count'],
            'y': real_admission
        }
        
        # 新しいデータをデータフレームに追加
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        
        # CSVファイルとして保存
        success = storage_manager.save_data(df, 'ultimate_pickup_data.csv')
        
        if success:
            return func.HttpResponse(
                json.dumps({"message": "データが正常に保存されました"}),
                status_code=200,
                mimetype="application/json"
            )
        else:
            return func.HttpResponse(
                json.dumps({"error": "データの保存に失敗しました"}),
                status_code=500,
                mimetype="application/json"
            )
    
    except Exception as e:
        logging.error(f"データ保存エラー: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"データ保存エラー: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        ) 