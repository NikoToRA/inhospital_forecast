from azure.storage.blob import BlobServiceClient
import pandas as pd
import json
from datetime import datetime
import os
import joblib
from dotenv import load_dotenv

class HospitalDataManager:
    def __init__(self):
        load_dotenv()
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.container_name = "hospital-data"
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.container_name)
        
        # コンテナが存在しない場合は作成
        try:
            self.container_client.get_container_properties()
        except:
            self.container_client.create_container()
    
    def get_hospital_data(self, hospital_id, year=None, month=None):
        """病院のデータを取得"""
        try:
            if year and month:
                blob_path = f"hospitals/{hospital_id}/admissions/{year}/{month}/data.csv"
            else:
                blob_path = f"hospitals/{hospital_id}/admissions/latest.csv"
            
            blob_client = self.container_client.get_blob_client(blob_path)
            data = blob_client.download_blob().readall()
            return pd.read_csv(pd.io.common.BytesIO(data))
        except:
            # データが存在しない場合は空のDataFrameを返す
            return pd.DataFrame()
    
    def add_new_data(self, hospital_id, data_df):
        """新しいデータを追加"""
        # 最新データの更新
        latest_path = f"hospitals/{hospital_id}/admissions/latest.csv"
        blob_client = self.container_client.get_blob_client(latest_path)
        blob_client.upload_blob(data_df.to_csv(index=False), overwrite=True)
        
        # 月次データの保存
        current_date = datetime.now()
        monthly_path = f"hospitals/{hospital_id}/admissions/{current_date.year}/{current_date.month:02d}/data.csv"
        blob_client = self.container_client.get_blob_client(monthly_path)
        blob_client.upload_blob(data_df.to_csv(index=False), overwrite=True)
    
    def get_hospital_metadata(self, hospital_id):
        """病院のメタデータを取得"""
        try:
            blob_path = f"hospitals/{hospital_id}/metadata.json"
            blob_client = self.container_client.get_blob_client(blob_path)
            data = blob_client.download_blob().readall()
            return json.loads(data)
        except:
            # メタデータが存在しない場合はデフォルト値を返す
            return {
                "hospital_id": hospital_id,
                "name": f"病院 {hospital_id}",
                "location": "未設定",
                "beds": 0,
                "created_at": datetime.now().strftime("%Y-%m-%d"),
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
    
    def update_hospital_metadata(self, hospital_id, metadata):
        """病院のメタデータを更新"""
        blob_path = f"hospitals/{hospital_id}/metadata.json"
        blob_client = self.container_client.get_blob_client(blob_path)
        blob_client.upload_blob(json.dumps(metadata, ensure_ascii=False), overwrite=True)
    
    def save_model(self, hospital_id, model):
        """モデルを保存"""
        blob_path = f"hospitals/{hospital_id}/models/latest_model.joblib"
        blob_client = self.container_client.get_blob_client(blob_path)
        model_data = joblib.dump(model, None)
        blob_client.upload_blob(model_data, overwrite=True)
    
    def load_model(self, hospital_id):
        """モデルを読み込み"""
        try:
            blob_path = f"hospitals/{hospital_id}/models/latest_model.joblib"
            blob_client = self.container_client.get_blob_client(blob_path)
            model_data = blob_client.download_blob().readall()
            return joblib.load(pd.io.common.BytesIO(model_data))
        except:
            return None
    
    def get_hospital_list(self):
        """登録されている病院のリストを取得"""
        try:
            blob_path = "hospitals/hospital_list.json"
            blob_client = self.container_client.get_blob_client(blob_path)
            data = blob_client.download_blob().readall()
            return json.loads(data)
        except:
            return []
    
    def update_hospital_list(self, hospital_list):
        """病院リストを更新"""
        blob_path = "hospitals/hospital_list.json"
        blob_client = self.container_client.get_blob_client(blob_path)
        blob_client.upload_blob(json.dumps(hospital_list, ensure_ascii=False), overwrite=True) 