import pandas as pd
import numpy as np
from datetime import datetime
import joblib
import os
try:
    from azure_storage import AzureStorageManager
except Exception as e:
    print(f"Azure Storage Managerのインポートに失敗しました: {e}")

class HospitalDataManager:
    def __init__(self, use_azure=False):
        # Azure Storage Managerの初期化
        self.use_azure = use_azure
        if self.use_azure:
            try:
                self.azure_manager = AzureStorageManager()
            except Exception as e:
                print(f"Azure Storage接続エラー: {e}")
                print("ローカルモードで実行します")
                self.use_azure = False
        
        # データ保存用のディレクトリを作成
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        self.hospital_list = []
        self.hospital_metadata = {}
        self.load_hospital_list()
        
        # モデルファイルのパス
        self.model_path = "fixed_rf_model.joblib"
    
    def load_hospital_list(self):
        """病院リストを読み込む"""
        try:
            if self.use_azure:
                hospital_list_df = self.azure_manager.download_data('hospital_list.csv')
            else:
                # ローカルファイルから読み込み
                hospital_list_path = os.path.join(self.data_dir, 'hospital_list.csv')
                if os.path.exists(hospital_list_path):
                    hospital_list_df = pd.read_csv(hospital_list_path)
                else:
                    hospital_list_df = None
            
            if hospital_list_df is not None:
                self.hospital_list = hospital_list_df.to_dict('records')
                for hospital in self.hospital_list:
                    self.hospital_metadata[hospital['hospital_id']] = hospital
            return True
        except Exception as e:
            print(f"Error loading hospital list: {e}")
            return False
    
    def get_hospital_list(self):
        """病院リストを取得"""
        return self.hospital_list
    
    def get_hospital_metadata(self, hospital_id):
        """病院のメタデータを取得"""
        return self.hospital_metadata.get(hospital_id)
    
    def update_hospital_metadata(self, hospital_id, metadata):
        """病院のメタデータを更新"""
        self.hospital_metadata[hospital_id] = metadata
        if self.use_azure:
            self.azure_manager.upload_data(
                pd.DataFrame([metadata]),
                f'hospitals/{hospital_id}/metadata.json'
            )
    
    def update_hospital_list(self, hospital_list):
        """病院リストを更新"""
        self.hospital_list = hospital_list
        hospital_list_df = pd.DataFrame(hospital_list)
        
        # ローカルファイルに保存
        hospital_list_path = os.path.join(self.data_dir, 'hospital_list.csv')
        hospital_list_df.to_csv(hospital_list_path, index=False)
        
        if self.use_azure:
            return self.azure_manager.upload_data(hospital_list_df, 'hospital_list.csv')
        return True
    
    def get_hospital_data(self, hospital_id):
        """病院のデータを取得"""
        try:
            if self.use_azure:
                return self.azure_manager.download_data(f'hospitals/{hospital_id}/admissions/latest.csv')
            else:
                # ローカルファイルから読み込み
                hospital_data_path = os.path.join(self.data_dir, f'{hospital_id}_data.csv')
                if os.path.exists(hospital_data_path):
                    return pd.read_csv(hospital_data_path)
                else:
                    # サンプルデータを生成
                    return self._generate_sample_data()
        except Exception as e:
            print(f"Error getting hospital data: {e}")
            return self._generate_sample_data()
    
    def _generate_sample_data(self):
        """サンプルデータを生成"""
        # 過去30日分のサンプルデータを生成
        dates = [datetime.now() - pd.Timedelta(days=i) for i in range(30)]
        data = {
            'date': dates,
            'total_outpatient': np.random.randint(400, 600, 30),
            'intro_outpatient': np.random.randint(10, 30, 30),
            'ER': np.random.randint(5, 20, 30),
            'bed_count': np.random.randint(250, 300, 30),
            'y': np.random.randint(270, 320, 30)
        }
        return pd.DataFrame(data)
    
    def save_prediction_data(self, date, outpatient, intro_outpatient, er_patients, bed_count, real_admission):
        """予測データを保存"""
        try:
            # 新しいデータを作成
            new_data = pd.DataFrame({
                'date': [date],
                'total_outpatient': [outpatient],
                'intro_outpatient': [intro_outpatient],
                'ER': [er_patients],
                'bed_count': [bed_count],
                'y': [real_admission]
            })
            
            # 既存のデータを読み込む
            training_data_path = os.path.join(self.data_dir, 'training_data.csv')
            if os.path.exists(training_data_path):
                existing_data = pd.read_csv(training_data_path)
                # 新しいデータを追加
                updated_data = pd.concat([existing_data, new_data], ignore_index=True)
            else:
                updated_data = new_data
            
            # ローカルファイルに保存
            updated_data.to_csv(training_data_path, index=False)
            
            # Azureにも保存
            if self.use_azure:
                try:
                    # 最新データとして保存
                    self.azure_manager.upload_data(
                        updated_data,
                        'training_data.csv'
                    )
                    
                    # 月次データとしても保存
                    current_date = datetime.now()
                    monthly_path = f"hospitals/admissions/{current_date.year}/{current_date.month:02d}/data.csv"
                    self.azure_manager.upload_data(
                        updated_data,
                        monthly_path
                    )
                    
                    return True, "データをローカルとAzureに保存しました"
                except Exception as e:
                    print(f"Azure保存エラー: {e}")
                    return True, "データをローカルに保存しました（Azureへの保存は失敗）"
            
            return True, "データをローカルに保存しました"
        except Exception as e:
            return False, f"エラーが発生しました: {e}"
    
    def load_model(self, hospital_id):
        """モデルを読み込む"""
        try:
            if self.use_azure:
                return self.azure_manager.download_model(f'hospitals/{hospital_id}/models/latest_model.joblib')
            else:
                # ローカルファイルから読み込み
                model_path = os.path.join(self.data_dir, 'fixed_rf_model.joblib')
                if os.path.exists(model_path):
                    return joblib.load(model_path)
                else:
                    model_path = self.model_path
                    if os.path.exists(model_path):
                        return joblib.load(model_path)
                    else:
                        print(f"モデルファイルが見つかりません: {model_path}")
                        return None
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    
    def save_model(self, model, hospital_id):
        """モデルを保存"""
        try:
            # ローカルに保存
            model_path = os.path.join(self.data_dir, 'fixed_rf_model.joblib')
            joblib.dump(model, model_path)
            
            # Azureにも保存
            if self.use_azure:
                try:
                    self.azure_manager.upload_model(
                        model,
                        f'hospitals/{hospital_id}/models/latest_model.joblib'
                    )
                    return True, "モデルをローカルとAzureに保存しました"
                except Exception as e:
                    print(f"Azure保存エラー: {e}")
                    return True, "モデルをローカルに保存しました（Azureへの保存は失敗）"
            
            return True, "モデルをローカルに保存しました"
        except Exception as e:
            return False, f"エラーが発生しました: {e}"
