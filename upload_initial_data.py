import os
import json
import pandas as pd
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

def upload_to_blob_storage(container_client, blob_name, data, is_binary=False):
    """データをBlob Storageにアップロード"""
    try:
        blob_client = container_client.get_blob_client(blob_name)
        if is_binary:
            blob_client.upload_blob(data, overwrite=True)
        else:
            blob_client.upload_blob(data.encode('utf-8'), overwrite=True)
        return True
    except Exception as e:
        print(f"Error uploading {blob_name}: {e}")
        return False

def initialize_storage():
    """初期データをAzure Blob Storageにアップロード"""
    # 環境変数の読み込み
    load_dotenv()
    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    
    # 接続文字列の確認
    if not connection_string:
        print("Error: Azure Storage接続文字列が設定されていません。")
        return False
    
    # 接続文字列の末尾にある不要な文字を削除
    connection_string = connection_string.strip()
    
    container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'hospital-data')
    
    print(f"Azure Storage接続を試みています...")
    
    try:
        # Blob Service Clientの初期化
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        
        # コンテナが存在しない場合は作成
        try:
            container_client.get_container_properties()
            print(f"コンテナ '{container_name}' が見つかりました。")
        except Exception as e:
            print(f"コンテナ '{container_name}' が見つかりません。新規作成します。")
            container_client.create_container()
        
        # 初期病院データの準備
        initial_hospital = {
            "hospital_id": "h001",
            "name": "札幌徳洲会病院",
            "location": "北海道札幌市厚別区大谷地東1丁目1-1",
            "beds": 310,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
        
        # 病院リストの準備
        hospital_list = [initial_hospital]
        
        print("病院リストをアップロードします...")
        
        # 病院リストのアップロード
        if upload_to_blob_storage(
            container_client,
            "hospital_list.csv",
            pd.DataFrame(hospital_list).to_csv(index=False)
        ):
            print("病院リストのアップロードに成功しました。")
        else:
            print("病院リストのアップロードに失敗しました。")
        
        print("病院メタデータをアップロードします...")
        
        # 病院メタデータのアップロード
        if upload_to_blob_storage(
            container_client,
            f"hospitals/{initial_hospital['hospital_id']}/metadata.json",
            json.dumps(initial_hospital, ensure_ascii=False)
        ):
            print("病院メタデータのアップロードに成功しました。")
        else:
            print("病院メタデータのアップロードに失敗しました。")
        
        # CSVデータのアップロード
        try:
            print("入院データをアップロードします...")
            df = pd.read_csv('ultimate_pickup_data.csv')
            csv_data = df.to_csv(index=False)
            if upload_to_blob_storage(
                container_client,
                f"hospitals/{initial_hospital['hospital_id']}/admissions/latest.csv",
                csv_data
            ):
                print("入院データ（最新版）のアップロードに成功しました。")
            else:
                print("入院データ（最新版）のアップロードに失敗しました。")
            
            # 月次データとしても保存
            print("月次データをアップロードします...")
            current_date = datetime.now()
            monthly_path = f"hospitals/{initial_hospital['hospital_id']}/admissions/{current_date.year}/{current_date.month:02d}/data.csv"
            if upload_to_blob_storage(
                container_client,
                monthly_path,
                csv_data
            ):
                print("月次データのアップロードに成功しました。")
            else:
                print("月次データのアップロードに失敗しました。")
        except Exception as e:
            print(f"CSVデータのアップロード中にエラーが発生しました: {e}")
        
        # モデルのアップロード
        try:
            print("予測モデルをアップロードします...")
            with open('fixed_rf_model.joblib', 'rb') as f:
                model_data = f.read()
            if upload_to_blob_storage(
                container_client,
                f"hospitals/{initial_hospital['hospital_id']}/models/latest_model.joblib",
                model_data,
                is_binary=True
            ):
                print("予測モデルのアップロードに成功しました。")
            else:
                print("予測モデルのアップロードに失敗しました。")
        except Exception as e:
            print(f"モデルのアップロード中にエラーが発生しました: {e}")
        
        print("初期データのアップロードが完了しました。")
        return True
    except Exception as e:
        print(f"Azure Storage接続エラー: {e}")
        return False

if __name__ == "__main__":
    initialize_storage() 