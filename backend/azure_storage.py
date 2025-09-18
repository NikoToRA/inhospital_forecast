import os
import joblib
import pandas as pd
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
import tempfile
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureStorageService:
    def __init__(self):
        """Azure Blob Storageクライアントを初期化"""
        self.connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
        self.container_name = os.environ.get('AZURE_STORAGE_CONTAINER', 'models')

        if not self.connection_string:
            logger.warning("Azure Storage connection string not found. Using local files.")
            self.blob_service_client = None
        else:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
                logger.info("Azure Blob Storage client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Azure Blob Storage: {e}")
                self.blob_service_client = None

    def download_model(self, model_filename='fixed_rf_model.joblib'):
        """
        Azure Blob StorageからMLモデルをダウンロード

        Args:
            model_filename (str): モデルファイル名

        Returns:
            model: ロードされたMLモデル、またはNone
        """
        if not self.blob_service_client:
            logger.info("Azure Storage not available, falling back to local model")
            return None

        try:
            # Blobクライアントを取得
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=model_filename
            )

            # 一時ファイルにダウンロード
            with tempfile.NamedTemporaryFile(delete=False, suffix='.joblib') as temp_file:
                download_stream = blob_client.download_blob()
                temp_file.write(download_stream.readall())
                temp_file_path = temp_file.name

            # モデルをロード
            model = joblib.load(temp_file_path)

            # 一時ファイルを削除
            os.unlink(temp_file_path)

            logger.info(f"Model {model_filename} downloaded and loaded successfully from Azure Storage")
            return model

        except ResourceNotFoundError:
            logger.warning(f"Model file {model_filename} not found in Azure Storage")
            return None
        except Exception as e:
            logger.error(f"Error downloading model from Azure Storage: {e}")
            return None

    def download_csv_data(self, csv_filename='ultimate_pickup_data.csv'):
        """
        Azure Blob StorageからCSVデータをダウンロード

        Args:
            csv_filename (str): CSVファイル名

        Returns:
            pd.DataFrame: CSVデータ、またはNone
        """
        if not self.blob_service_client:
            logger.info("Azure Storage not available, falling back to local CSV")
            return None

        try:
            # Blobクライアントを取得
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=csv_filename
            )

            # 一時ファイルにダウンロード
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w+b') as temp_file:
                download_stream = blob_client.download_blob()
                temp_file.write(download_stream.readall())
                temp_file_path = temp_file.name

            # CSVを読み込み
            df = pd.read_csv(temp_file_path)

            # 一時ファイルを削除
            os.unlink(temp_file_path)

            logger.info(f"CSV {csv_filename} downloaded successfully from Azure Storage")
            return df

        except ResourceNotFoundError:
            logger.warning(f"CSV file {csv_filename} not found in Azure Storage")
            return None
        except Exception as e:
            logger.error(f"Error downloading CSV from Azure Storage: {e}")
            return None

    def upload_model(self, model, model_filename='fixed_rf_model.joblib'):
        """
        MLモデルをAzure Blob Storageにアップロード

        Args:
            model: アップロードするMLモデル
            model_filename (str): モデルファイル名

        Returns:
            bool: アップロード成功かどうか
        """
        if not self.blob_service_client:
            logger.warning("Azure Storage not available, cannot upload model")
            return False

        try:
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.joblib') as temp_file:
                joblib.dump(model, temp_file.name)
                temp_file_path = temp_file.name

            # Blob Storageにアップロード
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=model_filename
            )

            with open(temp_file_path, 'rb') as data:
                blob_client.upload_blob(data, overwrite=True)

            # 一時ファイルを削除
            os.unlink(temp_file_path)

            logger.info(f"Model {model_filename} uploaded successfully to Azure Storage")
            return True

        except Exception as e:
            logger.error(f"Error uploading model to Azure Storage: {e}")
            return False

    def upload_csv_data(self, df, csv_filename='ultimate_pickup_data.csv'):
        """
        CSVデータをAzure Blob Storageにアップロード

        Args:
            df (pd.DataFrame): アップロードするDataFrame
            csv_filename (str): CSVファイル名

        Returns:
            bool: アップロード成功かどうか
        """
        if not self.blob_service_client:
            logger.warning("Azure Storage not available, cannot upload CSV")
            return False

        try:
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as temp_file:
                df.to_csv(temp_file.name, index=False)
                temp_file_path = temp_file.name

            # Blob Storageにアップロード
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=csv_filename
            )

            with open(temp_file_path, 'rb') as data:
                blob_client.upload_blob(data, overwrite=True)

            # 一時ファイルを削除
            os.unlink(temp_file_path)

            logger.info(f"CSV {csv_filename} uploaded successfully to Azure Storage")
            return True

        except Exception as e:
            logger.error(f"Error uploading CSV to Azure Storage: {e}")
            return False

    def list_blobs(self):
        """
        コンテナ内のBlobリストを取得

        Returns:
            list: Blobのリスト
        """
        if not self.blob_service_client:
            return []

        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            blobs = list(container_client.list_blobs())
            logger.info(f"Found {len(blobs)} blobs in container {self.container_name}")
            return [blob.name for blob in blobs]
        except Exception as e:
            logger.error(f"Error listing blobs: {e}")
            return []