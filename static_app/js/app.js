document.addEventListener('DOMContentLoaded', function() {
    // タブ切り替え機能
    setupTabs();
    
    // フォーム送信イベントの設定
    setupFormSubmit();
    
    // デバイス検出
    detectDeviceType();
    
    // 画面サイズ変更時のイベント設定
    window.addEventListener('resize', detectDeviceType);
});

// タブ切り替え機能の実装
function setupTabs() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // アクティブなタブのクラスを削除
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // クリックされたタブをアクティブに
            tab.classList.add('active');
            
            // 対応するコンテンツを表示
            const target = tab.getAttribute('data-target');
            document.getElementById(target).classList.add('active');
        });
    });
}

// モバイルデバイス検出
function detectDeviceType() {
    const width = window.innerWidth;
    const isMobile = width < 768; // 768px未満をモバイルと判定
    
    // モバイル向けのスタイル調整
    if (isMobile) {
        document.body.classList.add('mobile');
    } else {
        document.body.classList.remove('mobile');
    }
    
    return isMobile;
}

// 入院予測フォームの設定
function setupFormSubmit() {
    const predictionForm = document.getElementById('prediction-form');
    if (predictionForm) {
        predictionForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            // フォームからデータを取得
            const formData = new FormData(predictionForm);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value;
            });
            
            // 予測API呼び出し
            predictAdmission(data);
        });
    }
}

// 入院予測APIの呼び出し
function predictAdmission(data) {
    // 結果表示領域をクリア
    const resultDisplay = document.getElementById('prediction-result');
    resultDisplay.textContent = '予測中...';
    
    // APIエンドポイント
    const apiUrl = '/api/predict';
    
    // APIリクエスト
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('APIリクエストが失敗しました');
        }
        return response.json();
    })
    .then(result => {
        // 結果を表示
        displayPredictionResult(result);
    })
    .catch(error => {
        resultDisplay.textContent = `エラーが発生しました: ${error.message}`;
        console.error('Error:', error);
    });
}

// 予測結果の表示
function displayPredictionResult(result) {
    const resultDisplay = document.getElementById('prediction-result');
    
    if (result.error) {
        resultDisplay.textContent = `エラー: ${result.error}`;
        return;
    }
    
    // 結果をフォーマットして表示
    let formattedResult = "";
    if (result.prediction !== undefined) {
        formattedResult += `予測入院日数: ${result.prediction} 日\n`;
    }
    
    if (result.confidence_interval) {
        formattedResult += `信頼区間: ${result.confidence_interval[0]} - ${result.confidence_interval[1]} 日\n`;
    }
    
    if (result.feature_importance) {
        formattedResult += "\n特徴量の重要度:\n";
        for (const [feature, importance] of Object.entries(result.feature_importance)) {
            formattedResult += `${feature}: ${importance.toFixed(4)}\n`;
        }
    }
    
    resultDisplay.textContent = formattedResult;
}

// データ取得API呼び出し
function fetchData() {
    const dataDisplay = document.getElementById('data-result');
    if (dataDisplay) {
        dataDisplay.textContent = 'データ取得中...';
        
        fetch('/api/data')
            .then(response => {
                if (!response.ok) {
                    throw new Error('データの取得に失敗しました');
                }
                return response.json();
            })
            .then(data => {
                dataDisplay.textContent = JSON.stringify(data, null, 2);
            })
            .catch(error => {
                dataDisplay.textContent = `エラーが発生しました: ${error.message}`;
                console.error('Error:', error);
            });
    }
} 