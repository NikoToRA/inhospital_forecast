# Azure Web Appデプロイ確認事項

## デプロイ後の初期確認

1. **アプリケーションの起動確認**
   - アプリケーションURLにアクセスし、正常に表示されるか確認する
   - `/healthcheck`エンドポイントにアクセスして、ヘルスチェックが成功するか確認する

2. **ログの確認**
   - Azure Portalのログストリームでエラーがないことを確認する
   - アプリケーションのログファイル（/LogFiles/application.log）を確認する

3. **ストレージ接続の確認**
   - Azure Blob Storageへの接続が成功しているか確認する
   - ログにストレージ関連のエラーがないことを確認する

## 設定項目の確認

1. **環境変数**
   - `AZURE_STORAGE_CONNECTION_STRING` - Azure Storageの接続文字列
   - `AZURE_STORAGE_CONTAINER_NAME` - 'hospital-data'
   - `USE_AZURE` - 'true'
   - `PYTHON_ENABLE_WORKER_EXTENSIONS` - '1'
   - `STREAMLIT_SERVER_HEADLESS` - 'true'
   - `WEBSITE_RUN_FROM_PACKAGE` - '0'
   - `SCM_DO_BUILD_DURING_DEPLOYMENT` - 'true'

2. **ストレージコンテナ構成**
   - `hospital-data`コンテナが存在することを確認
   - 必要なデータファイルが正しくアップロードされていることを確認:
     - fixed_rf_model.joblib
     - hospital_list.csv
     - training_data.csv (存在する場合)

## トラブルシューティング

1. **アプリケーションが起動しない場合**
   - ログを確認して具体的なエラーを特定する
   - 環境変数が正しく設定されているか確認する
   - 必要なファイルがすべてデプロイされたか確認する

2. **ストレージ接続エラー**
   - 接続文字列が正しいか確認する
   - Azure Storageアカウントのファイアウォール設定を確認する
   - コンテナへのアクセス権限を確認する

3. **日本語フォントの問題**
   - 必要なフォントパッケージをインストールする場合は、カスタムスクリプトを追加
   - フォントの代替設定が機能しているか確認する

4. **メモリ・パフォーマンスの問題**
   - App Serviceプランのスケールアップを検討する
   - P1v2以上のプランを使用することを推奨

## 定期メンテナンス

1. **定期的なバックアップ**
   - Azure Blob Storageのデータを定期的にバックアップする
   - データの整合性を確認する

2. **パフォーマンス監視**
   - Application Insightsでパフォーマンスを監視する
   - メモリ使用量、CPU使用率を監視する

3. **セキュリティアップデート**
   - 定期的にセキュリティアップデートを適用する
   - 依存パッケージのバージョン更新を検討する 