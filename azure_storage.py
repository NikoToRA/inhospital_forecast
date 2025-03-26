from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
import pandas as pd
import joblib
from io import BytesIO
import json
import traceback

class AzureStorageManager:
    def __init__(self):
        load_dotenv()
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not connection_string:
            raise ValueError("Azure Storage connection string not found in environment variables")
        
        # 接続文字列の末尾にある不要な文字を削除
        connection_string = connection_string.strip()
        
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            self.container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME', 'hospital-data')
            
            # コンテナの存在確認
            try:
                self.blob_service_client.get_container_client(self.container_name).get_container_properties()
                print(f"コンテナ {self.container_name} に接続成功")
            except Exception as e:
                print(f"コンテナ {self.container_name} が見つかりません: {e}")
                try:
                    self.blob_service_client.get_container_client(self.container_name).create_container()
                    print(f"コンテナ {self.container_name} を作成しました")
                except Exception as create_error:
                    error_details = traceback.format_exc()
                    print(f"コンテナの作成に失敗しました: {create_error}\n{error_details}")
                    raise ValueError(f"Azure Storage container could not be created: {create_error}")
        except Exception as conn_error:
            error_details = traceback.format_exc()
            print(f"Azure Storageへの接続に失敗しました: {conn_error}\n{error_details}")
            raise ValueError(f"Azure Storage connection failed: {conn_error}")
    
    def download_model(self, model_name='model.joblib'):
        """モデルをダウンロードする"""
        try:
            blob_client = self.blob_service_client.get_container_client(self.container_name).get_blob_client(model_name)
            model_data = blob_client.download_blob().readall()
            return joblib.load(BytesIO(model_data))
        except Exception as e:
            print(f"Error downloading model: {e}")
            return None
    
    def download_data(self, filename='hospital_data.csv'):
        """データをダウンロードする"""
        try:
            blob_client = self.blob_service_client.get_container_client(self.container_name).get_blob_client(filename)
            data = blob_client.download_blob().readall()
            
            # ファイル形式に応じた処理
            if filename.endswith('.csv'):
                return pd.read_csv(BytesIO(data))
            elif filename.endswith('.json'):
                return pd.DataFrame([json.loads(data.decode('utf-8'))])
            else:
                print(f"未対応のファイル形式です: {filename}")
                return None
        except Exception as e:
            print(f"Error downloading data: {e}")
            return None
    
    def upload_data(self, data, filename='hospital_data.csv'):
        """データをアップロードする"""
        try:
            # ディレクトリが存在しない場合は作成
            path_parts = filename.split('/')
            if len(path_parts) > 1:
                # 階層構造を持つパスの場合、ディレクトリを作成
                directory = '/'.join(path_parts[:-1])
                # Blobストレージには明示的なディレクトリ作成は不要
            
            # データ形式に応じた処理
            if isinstance(data, pd.DataFrame):
                # DataFrameをCSVに変換
                content = data.to_csv(index=False).encode('utf-8')
            elif isinstance(data, dict) or isinstance(data, list):
                # 辞書またはリストをJSONに変換
                content = json.dumps(data, ensure_ascii=False).encode('utf-8')
            elif isinstance(data, str):
                # 文字列をエンコード
                content = data.encode('utf-8')
            else:
                # その他のデータ型はエラー
                raise ValueError(f"Unsupported data type: {type(data)}")
            
            # BlobClientを取得
            blob_client = self.blob_service_client.get_container_client(self.container_name).get_blob_client(filename)
            
            # データをアップロード
            blob_client.upload_blob(content, overwrite=True)
            return True
        except Exception as e:
            print(f"Error uploading data: {e}")
            return False
    
    def upload_model(self, model, model_name='model.joblib'):
        """モデルをアップロードする"""
        try:
            # モデルをバイトデータに変換
            model_bytes = BytesIO()
            joblib.dump(model, model_bytes)
            model_bytes.seek(0)
            
            # ディレクトリが存在しない場合は作成
            path_parts = model_name.split('/')
            if len(path_parts) > 1:
                # 階層構造を持つパスの場合、ディレクトリを作成
                directory = '/'.join(path_parts[:-1])
                # Blobストレージには明示的なディレクトリ作成は不要
            
            # BlobClientを取得
            blob_client = self.blob_service_client.get_container_client(self.container_name).get_blob_client(model_name)
            
            # モデルをアップロード
            blob_client.upload_blob(model_bytes.read(), overwrite=True)
            return True
        except Exception as e:
            print(f"Error uploading model: {e}")
            return False
            
    def list_blobs(self, prefix=None):
        """Blobのリストを取得する"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            blobs = container_client.list_blobs(name_starts_with=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            print(f"Error listing blobs: {e}")
            return []
    
    def delete_blob(self, blob_name):
        """Blobを削除する"""
        try:
            blob_client = self.blob_service_client.get_container_client(self.container_name).get_blob_client(blob_name)
            blob_client.delete_blob()
            return True
        except Exception as e:
            print(f"Error deleting blob: {e}")
            return False 