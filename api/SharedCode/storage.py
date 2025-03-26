import os
import pandas as pd
import joblib
from io import BytesIO
import json
import logging
from azure.storage.blob import BlobServiceClient

class AzureStorageManager:
    def __init__(self):
        """
        Azure Blob Storageを使用してデータとモデルを管理するクラス
        """
        # 環境変数から接続文字列を取得
        connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
        container_name = os.environ.get('AZURE_STORAGE_CONTAINER_NAME', 'hospital-strage')  # 注意: hospital-strageに修正
        
        if not connection_string:
            logging.error("Azure Storage connection string not found in environment variables")
            raise ValueError("Azure Storage connection string not found in environment variables")
        
        try:
            # Azure Blob Serviceクライアントの初期化
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            self.container_name = container_name
            logging.info(f"AzureStorageManager initialized with container: {container_name}")
            
            # コンテナの存在確認
            self.blob_service_client.get_container_client(self.container_name).get_container_properties()
        except Exception as e:
            logging.error(f"Azure Blob Storage connection error: {str(e)}")
            raise
    
    def load_model(self, model_name):
        """
        モデルファイルをロードする
        
        Args:
            model_name (str): モデルファイル名
            
        Returns:
            object: ロードされたモデル、失敗した場合はNone
        """
        try:
            logging.info(f"Loading model: {model_name}")
            blob_client = self.blob_service_client.get_container_client(self.container_name).get_blob_client(model_name)
            
            # モデルをダウンロード
            model_data = blob_client.download_blob().readall()
            
            # BytesIOを使用してメモリ上でモデルをロード
            return joblib.load(BytesIO(model_data))
        except Exception as e:
            logging.error(f"Error loading model {model_name}: {str(e)}")
            return None
    
    def load_data(self, filename):
        """
        CSVデータをロードする
        
        Args:
            filename (str): CSVファイル名
            
        Returns:
            pandas.DataFrame: ロードされたデータフレーム、失敗した場合はNone
        """
        try:
            logging.info(f"Loading data: {filename}")
            blob_client = self.blob_service_client.get_container_client(self.container_name).get_blob_client(filename)
            
            # CSVデータをダウンロード
            data = blob_client.download_blob().readall()
            
            # BytesIOを使用してメモリ上でCSVをロード
            return pd.read_csv(BytesIO(data))
        except Exception as e:
            logging.error(f"Error loading data {filename}: {str(e)}")
            return None
    
    def save_data(self, data, filename):
        """
        データを保存する
        
        Args:
            data (pandas.DataFrame): 保存するデータフレーム
            filename (str): 保存先ファイル名
            
        Returns:
            bool: 成功した場合はTrue、失敗した場合はFalse
        """
        try:
            logging.info(f"Saving data to: {filename}")
            blob_client = self.blob_service_client.get_container_client(self.container_name).get_blob_client(filename)
            
            # DataFrameをCSVに変換
            csv_data = data.to_csv(index=False).encode('utf-8')
            
            # アップロード
            blob_client.upload_blob(csv_data, overwrite=True)
            logging.info(f"Data saved successfully to {filename}")
            return True
        except Exception as e:
            logging.error(f"Error saving data to {filename}: {str(e)}")
            return False 