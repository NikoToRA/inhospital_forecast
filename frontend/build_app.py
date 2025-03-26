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
        form {
            margin-top: 20px;
            text-align: left;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 4px;
        }
        label {
            display: block;
            margin-bottom: 5px;
        }
        input, select {
            width: 100%;
            padding: 8px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background-color: #0078d4;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
    </style>
    <script>
        // 予測API用のスクリプト
        function submitPrediction(event) {
            event.preventDefault();
            const form = document.getElementById('predictionForm');
            const formData = new FormData(form);
            const data = {};
            
            formData.forEach((value, key) => {
                data[key] = value;
            });
            
            // APIにPOSTリクエストを送信
            fetch('/api/PredictFunction', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('predictionResult').textContent = JSON.stringify(data, null, 2);
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('predictionResult').textContent = 'エラーが発生しました: ' + error;
            });
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>InHospital Forecast</h1>
        <p>
            この静的Webサイトは、Azure Static Web Appsにデプロイされています。<br>
            APIへのアクセスは、この静的ページを通じて行われます。
        </p>
        
        <h2>データ取得API</h2>
        <a href="/api/DataFunction" class="button">データ取得APIへアクセス</a>
        
        <h2>予測API</h2>
        <form id="predictionForm" onsubmit="submitPrediction(event)">
            <label for="age">年齢:</label>
            <input type="number" id="age" name="age" min="0" max="120" required>
            
            <label for="gender">性別:</label>
            <select id="gender" name="gender" required>
                <option value="男性">男性</option>
                <option value="女性">女性</option>
            </select>
            
            <label for="diagnosis">診断名:</label>
            <input type="text" id="diagnosis" name="diagnosis" required>
            
            <button type="submit">予測する</button>
        </form>
        
        <h3>予測結果:</h3>
        <pre id="predictionResult" style="text-align: left; background: #eee; padding: 10px; border-radius: 4px;"></pre>
    </div>
</body>
</html>
        """)
    
    print("ビルドが完了しました。")
    return True

if __name__ == "__main__":
    success = build_streamlit_app()
    sys.exit(0 if success else 1) 