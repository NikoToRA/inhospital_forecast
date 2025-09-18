import os
import tempfile
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import joblib

class BlobStorageService:
    """
    Azure Blob Storageサービス
    """
    def __init__(self):
        """
        BlobStorageServiceの初期化
        環境変数から接続情報を取得する
        """
        # 環境変数から取得
        self.connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME", "inhospital-forecast")
        
        # 接続文字列がある場合は接続を確立
        if self.connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
            self.is_connected = True
        else:
            self.is_connected = False
            print("警告: Azure Blob Storageの接続文字列が設定されていません。ローカルファイルを使用します。")
    
    def download_blob_to_temp(self, blob_name):
        """
        BlobStorageからファイルをダウンロードして一時ファイルとして保存
        
        Args:
            blob_name (str): Blob名
            
        Returns:
            str: 一時ファイルのパス、エラー時はNone
        """
        if not self.is_connected:
            return None
            
        try:
            # 一時ファイルを作成
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Blobをダウンロード
            blob_client = self.container_client.get_blob_client(blob_name)
            with open(temp_file_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            return temp_file_path
        except Exception as e:
            print(f"Blobダウンロード中にエラーが発生しました: {e}")
            return None
    
    def load_model_from_blob(self, model_blob_name):
        """
        BlobStorageからモデルをロードする
        
        Args:
            model_blob_name (str): モデルのBlob名
            
        Returns:
            object: ロードされたモデル、エラー時はNone
        """
        if not self.is_connected:
            return None
            
        try:
            # モデルを一時ファイルとしてダウンロード
            temp_model_path = self.download_blob_to_temp(model_blob_name)
            
            if temp_model_path:
                # モデルをロード
                model = joblib.load(temp_model_path)
                
                # 一時ファイルを削除
                os.unlink(temp_model_path)
                
                return model
            else:
                return None
        except Exception as e:
            print(f"モデルロード中にエラーが発生しました: {e}")
            return None
    
    def load_csv_from_blob(self, csv_blob_name):
        """
        BlobStorageからCSVファイルをロードする
        
        Args:
            csv_blob_name (str): CSVファイルのBlob名
            
        Returns:
            str: CSVファイルの一時パス、エラー時はNone
        """
        if not self.is_connected:
            return None
            
        try:
            # CSVファイルを一時ファイルとしてダウンロード
            temp_csv_path = self.download_blob_to_temp(csv_blob_name)
            
            if temp_csv_path:
                return temp_csv_path
            else:
                return None
        except Exception as e:
            print(f"CSVファイルロード中にエラーが発生しました: {e}")
            return None 