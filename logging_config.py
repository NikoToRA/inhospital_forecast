import logging
import sys
import os

def setup_logging():
    """アプリケーションのロギング設定を行います"""
    
    # ロギングレベルを環境変数から取得（デフォルトはINFO）
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # 基本設定
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # ルートロガーの取得
    logger = logging.getLogger()
    
    # Azure環境で実行している場合の特別な設定
    if os.environ.get('WEBSITE_SITE_NAME'):
        logger.info("Azure Web App環境で実行中")
        
        # ファイルハンドラを追加（Azure Web Appのログファイル）
        log_dir = os.environ.get('HOME', '') + "/LogFiles"
        if os.path.exists(log_dir):
            try:
                file_handler = logging.FileHandler(log_dir + "/application.log")
                file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                logger.addHandler(file_handler)
                logger.info("ファイルログハンドラを追加しました: %s", log_dir + "/application.log")
            except Exception as e:
                logger.error("ファイルログハンドラの追加に失敗: %s", str(e))
    
    # 主要なライブラリのログレベルを調整
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('streamlit').setLevel(logging.INFO)
    
    return logger

# メインロガーの取得
logger = setup_logging() 