import os
import shutil
import subprocess
import sys

def build_streamlit_app():
    """
    Streamlitアプリケーションを静的HTMLにビルドする
    """
    print("Streamlitアプリをビルドしています...")
    
    # 出力ディレクトリを作成/クリアする
    build_dir = "build"
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    
    # index.htmlファイルを作成
    with open(os.path.join(build_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write("""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InHospital Forecast</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background-color: #f5f5f5;
            text-align: center;
        }
        .container {
            max-width: 800px;
            padding: 20px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
        }
        p {
            color: #666;
            line-height: 1.6;
        }
        .button {
            display: inline-block;
            background-color: #0078d4;
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            text-decoration: none;
            margin-top: 20px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>InHospital Forecast</h1>
        <p>
            この静的Webサイトは、Azure Static Web Appsにデプロイされています。<br>
            APIへのアクセスは、この静的ページを通じて行われます。
        </p>
        <a href="/api/DataFunction" class="button">データ取得APIへアクセス</a>
        <br>
        <a href="/api/PredictFunction" class="button">予測APIへアクセス</a>
    </div>
</body>
</html>
        """)
    
    print("ビルドが完了しました。")
    return True

if __name__ == "__main__":
    success = build_streamlit_app()
    sys.exit(0 if success else 1) 