// APIリクエスト関数
async function apiRequest(endpoint, method, data = null) {
    try {
        const url = `/api${endpoint}`;
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API request failed: ${response.status} ${response.statusText} - ${errorText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// 日付情報を更新する関数
function updateDateInfo(date) {
    const dateInfo = document.getElementById('date-info');
    if (!dateInfo) return;
    
    const dayOfWeek = ['日曜日', '月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日'][date.getDay()];
    const formattedDate = `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
    
    dateInfo.innerHTML = `<strong>${formattedDate}（${dayOfWeek}）</strong>`;
    
    // 土日の場合は色を変える（実際の祝日判定はサーバーサイドで行う）
    if (date.getDay() === 0 || date.getDay() === 6) {
        dateInfo.innerHTML += '<div class="holiday-badge">休日です</div>';
    }
}

// 週間予測グラフを表示する関数
function displayWeeklyChart(weeklyData) {
    const ctx = document.getElementById('weekly-chart-canvas').getContext('2d');
    
    // 既存のチャートがあれば破棄
    if (window.weeklyChart) {
        window.weeklyChart.destroy();
    }
    
    const labels = weeklyData.map(item => `${item.日付}\n(${item.曜日})`);
    const values = weeklyData.map(item => item.予測入院患者数);
    
    window.weeklyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '予測入院患者数',
                data: values,
                backgroundColor: '#00467F',
                borderColor: '#00467F',
                borderWidth: 2,
                pointBackgroundColor: '#00467F',
                pointRadius: 5,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `予測入院患者数: ${context.raw.toFixed(1)}人`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: '予測入院患者数'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '日付'
                    }
                }
            }
        }
    });
}

// シナリオ比較グラフを表示する関数
function displayScenarioComparison(results) {
    // テーブルに結果を表示
    const comparisonTable = document.getElementById('scenario-comparison-table').querySelector('tbody');
    comparisonTable.innerHTML = '';
    
    results.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.シナリオ}</td>
            <td>${item.日付}</td>
            <td>${item.曜日}</td>
            <td>${item.予測入院患者数.toFixed(1)}</td>
        `;
        comparisonTable.appendChild(row);
    });
    
    // グラフに結果を表示
    const ctx = document.getElementById('comparison-chart-canvas').getContext('2d');
    
    // 既存のチャートがあれば破棄
    if (window.comparisonChart) {
        window.comparisonChart.destroy();
    }
    
    const labels = results.map(item => `${item.シナリオ}\n${item.日付}\n(${item.曜日})`);
    const values = results.map(item => item.予測入院患者数);
    
    window.comparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '予測入院患者数',
                data: values,
                backgroundColor: '#00467F',
                borderColor: '#00467F',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `予測入院患者数: ${context.raw.toFixed(1)}人`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: '予測入院患者数'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'シナリオ'
                    }
                }
            }
        }
    });
    
    // 結果を表示
    document.getElementById('scenario-comparison-result').classList.remove('hidden');
}

// カスタムシナリオのフォームを更新する関数
function updateCustomScenarios() {
    const numScenarios = parseInt(document.getElementById('num-scenarios').value);
    const container = document.getElementById('custom-scenarios-container');
    
    if (!container) return;
    
    container.innerHTML = '';
    
    for (let i = 1; i <= numScenarios; i++) {
        const scenarioDiv = document.createElement('div');
        scenarioDiv.className = 'scenario-form';
        scenarioDiv.innerHTML = `
            <h3>シナリオ ${i}</h3>
            <div class="form-row">
                <div class="form-column">
                    <div class="form-group">
                        <label for="scenario-name-${i}">シナリオ名</label>
                        <input type="text" id="scenario-name-${i}" class="form-control" value="シナリオ ${i}">
                    </div>
                    <div class="form-group">
                        <label for="scenario-date-${i}">日付</label>
                        <input type="date" id="scenario-date-${i}" class="form-control">
                    </div>
                </div>
                <div class="form-column">
                    <div class="form-group">
                        <label for="scenario-total-outpatient-${i}">前日総外来患者数</label>
                        <input type="number" id="scenario-total-outpatient-${i}" class="form-control" min="0" value="500">
                    </div>
                    <div class="form-group">
                        <label for="scenario-intro-outpatient-${i}">前日紹介外来患者数</label>
                        <input type="number" id="scenario-intro-outpatient-${i}" class="form-control" min="0" value="20">
                    </div>
                    <div class="form-group">
                        <label for="scenario-er-count-${i}">前日救急搬送患者数</label>
                        <input type="number" id="scenario-er-count-${i}" class="form-control" min="0" value="15">
                    </div>
                    <div class="form-group">
                        <label for="scenario-bed-count-${i}">現在の病床利用数</label>
                        <input type="number" id="scenario-bed-count-${i}" class="form-control" min="0" value="280">
                    </div>
                </div>
            </div>
            <div class="divider"></div>
        `;
        
        container.appendChild(scenarioDiv);
        
        // 日付の初期値を設定
        const today = new Date();
        today.setDate(today.getDate() + i - 1);
        document.getElementById(`scenario-date-${i}`).valueAsDate = today;
    }
}

// 月間カレンダーを表示する関数
function displayMonthlyCalendar(predictions, year, month) {
    const container = document.getElementById('monthly-calendar');
    if (!container) return;
    
    // 月の日数を取得
    const daysInMonth = new Date(year, month, 0).getDate();
    
    // 月の最初の日の曜日を取得（0: 日曜日, 1: 月曜日, ..., 6: 土曜日）
    const firstDay = new Date(year, month - 1, 1).getDay();
    
    // カレンダーのHTML生成
    let calendarHTML = `
        <h3>${year}年 ${month}月 入院患者数予測</h3>
        <table class="calendar-table">
            <thead>
                <tr>
                    <th>日</th>
                    <th>月</th>
                    <th>火</th>
                    <th>水</th>
                    <th>木</th>
                    <th>金</th>
                    <th>土</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    // 日付カウンター
    let day = 1;
    
    // 週ごとの行を生成
    for (let i = 0; i < 6; i++) {
        calendarHTML += '<tr>';
        
        // 曜日ごとのセルを生成
        for (let j = 0; j < 7; j++) {
            if ((i === 0 && j < firstDay) || day > daysInMonth) {
                // 月の最初の週で、月の最初の日より前の曜日、または月の最後の日を超えた場合は空セル
                calendarHTML += '<td></td>';
            } else {
                // 予測データを取得
                const dateStr = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
                const prediction = predictions.find(p => p.date === dateStr);
                
                if (prediction) {
                    // 混雑度に応じたクラスを設定
                    let busynessClass = '';
                    switch (prediction.busyness_level) {
                        case '少ない':
                            busynessClass = 'busyness-low';
                            break;
                        case 'やや少ない':
                            busynessClass = 'busyness-medium-low';
                            break;
                        case 'やや多い':
                            busynessClass = 'busyness-medium-high';
                            break;
                        case '多い':
                            busynessClass = 'busyness-high';
                            break;
                    }
                    
                    // 日付セルを生成
                    calendarHTML += `
                        <td class="calendar-day ${busynessClass}">
                            <div class="day-number">${day}</div>
                            <div class="busyness-level">${prediction.busyness_level}</div>
                            <div class="prediction-value">${Math.round(prediction.prediction)}人</div>
                        </td>
                    `;
                } else {
                    // 予測データがない場合は日付のみ表示
                    calendarHTML += `
                        <td class="calendar-day">
                            <div class="day-number">${day}</div>
                        </td>
                    `;
                }
                
                day++;
            }
        }
        
        calendarHTML += '</tr>';
        
        // 月の最後の日を超えたら終了
        if (day > daysInMonth) {
            break;
        }
    }
    
    calendarHTML += `
            </tbody>
        </table>
        <div class="calendar-legend">
            <div class="legend-item">
                <span class="legend-color busyness-low"></span>
                <span class="legend-label">少ない</span>
            </div>
            <div class="legend-item">
                <span class="legend-color busyness-medium-low"></span>
                <span class="legend-label">やや少ない</span>
            </div>
            <div class="legend-item">
                <span class="legend-color busyness-medium-high"></span>
                <span class="legend-label">やや多い</span>
            </div>
            <div class="legend-item">
                <span class="legend-color busyness-high"></span>
                <span class="legend-label">多い</span>
            </div>
        </div>
    `;
    
    container.innerHTML = calendarHTML;
}

// タブ1: 単一予測の初期化
function initializeSinglePrediction() {
    const predictionDateInput = document.getElementById('prediction-date');
    const predictButton = document.getElementById('predict-button');
    
    // 日付入力の初期値を今日に設定
    if (predictionDateInput) {
        const today = new Date();
        predictionDateInput.valueAsDate = today;
        updateDateInfo(today);
        
        // 日付変更時の処理
        predictionDateInput.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            updateDateInfo(selectedDate);
        });
    }
    
    // 予測実行ボタンのイベント
    if (predictButton) {
        predictButton.addEventListener('click', async function() {
            const date = document.getElementById('prediction-date').value;
            const totalOutpatient = document.getElementById('total-outpatient').value;
            const introOutpatient = document.getElementById('intro-outpatient').value;
            const erCount = document.getElementById('er-count').value;
            const bedCount = document.getElementById('bed-count').value;
            
            // 入力値の検証
            if (!date || !totalOutpatient || !introOutpatient || !erCount || !bedCount) {
                alert('すべての項目を入力してください');
                return;
            }
            
            try {
                // ローディング表示
                predictButton.disabled = true;
                predictButton.textContent = '予測中...';
                
                const data = {
                    date: date,
                    total_outpatient: totalOutpatient,
                    intro_outpatient: introOutpatient,
                    er_count: erCount,
                    bed_count: bedCount
                };
                
                // APIリクエスト
                const result = await apiRequest('/predict', 'POST', data);
                
                if (result) {
                    // 予測結果を表示（さらに詳細なコンソールログを追加）
                    console.log("予測結果オブジェクト:", result);
                    console.log("予測値:", result.prediction);
                    console.log("週間予測:", result.weekly_forecast);
                    
                    // 予測値が数値かどうか確認
                    if (typeof result.prediction === 'number') {
                        const predictionValueElement = document.getElementById('prediction-value');
                        console.log("予測値表示要素:", predictionValueElement);
                        if (predictionValueElement) {
                            predictionValueElement.textContent = result.prediction.toFixed(1);
                            console.log("予測値を設定しました:", result.prediction.toFixed(1));
                        } else {
                            console.error("予測値表示要素が見つかりません");
                        }
                    } else {
                        console.error("予測値が数値ではありません:", result.prediction);
                        document.getElementById('prediction-value').textContent = "エラー";
                    }
                    
                    // 週間予測をテーブルに表示
                    const weeklyTable = document.getElementById('weekly-forecast-table').querySelector('tbody');
                    weeklyTable.innerHTML = '';
                    
                    result.weekly_forecast.forEach(item => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${item.日付}</td>
                            <td>${item.曜日}</td>
                            <td>${item.予測入院患者数.toFixed(1)}</td>
                        `;
                        weeklyTable.appendChild(row);
                    });
                    
                    // 週間予測をグラフに表示
                    displayWeeklyChart(result.weekly_forecast);
                    
                    // 結果を表示（さらに詳細なデバッグログを追加）
                    const predictionResult = document.getElementById('prediction-result');
                    console.log("予測結果要素:", predictionResult);
                    if (predictionResult) {
                        console.log("予測結果要素の表示前のクラス:", predictionResult.className);
                        console.log("予測結果要素のスタイル:", predictionResult.style.display);
                        
                        // hiddenクラスを削除
                        predictionResult.classList.remove('hidden');
                        
                        // 直接スタイルも設定
                        predictionResult.style.display = 'block';
                        
                        console.log("予測結果要素の表示後のクラス:", predictionResult.className);
                        console.log("予測結果要素の表示後のスタイル:", predictionResult.style.display);
                    } else {
                        console.error("予測結果要素が見つかりません");
                    }
                }
            } catch (error) {
                console.error('Prediction error:', error);
                alert(`予測中にエラーが発生しました: ${error.message}`);
            } finally {
                predictButton.disabled = false;
                predictButton.textContent = '予測実行';
            }
        });
    }
    
    // 予測結果保存ボタンのイベント
    const savePredictionButton = document.getElementById('save-prediction-button');
    if (savePredictionButton) {
        savePredictionButton.addEventListener('click', function() {
            document.getElementById('save-form').classList.remove('hidden');
            
            // 予測値を実際の入院患者数の初期値として設定
            const predictionValue = parseFloat(document.getElementById('prediction-value').textContent);
            document.getElementById('real-admission').value = predictionValue;
        });
    }
    
    // 確定して保存ボタンのイベント
    const confirmSaveButton = document.getElementById('confirm-save-button');
    if (confirmSaveButton) {
        confirmSaveButton.addEventListener('click', async function() {
            const realAdmission = document.getElementById('real-admission').value;
            
            if (!realAdmission) {
                alert('実際の入院患者数を入力してください');
                return;
            }
            
            try {
                confirmSaveButton.disabled = true;
                confirmSaveButton.textContent = '保存中...';
                
                // 保存処理（APIエンドポイントは実装されていないため、ここではアラートのみ）
                alert('データが保存されました（デモ表示）');
                
                // フォームを隠す
                document.getElementById('save-form').classList.add('hidden');
            } catch (error) {
                console.error('Save error:', error);
                alert(`データの保存中にエラーが発生しました: ${error.message}`);
            } finally {
                confirmSaveButton.disabled = false;
                confirmSaveButton.textContent = '確定して保存';
            }
        });
    }
}

// タブ2: 月間カレンダーの初期化
function initializeMonthlyCalendar() {
    const showCalendarButton = document.getElementById('show-calendar-button');
    
    if (showCalendarButton) {
        showCalendarButton.addEventListener('click', async function() {
            const year = document.getElementById('calendar-year').value;
            const month = document.getElementById('calendar-month').value;
            const avgTotalOutpatient = document.getElementById('avg-total-outpatient').value;
            const avgIntroOutpatient = document.getElementById('avg-intro-outpatient').value;
            const avgEr = document.getElementById('avg-er').value;
            const avgBedCount = document.getElementById('avg-bed-count').value;
            
            // 入力値の検証
            if (!year || !month || !avgTotalOutpatient || !avgIntroOutpatient || !avgEr || !avgBedCount) {
                alert('すべての項目を入力してください');
                return;
            }
            
            try {
                // ローディング表示
                showCalendarButton.disabled = true;
                showCalendarButton.textContent = 'カレンダー作成中...';
                
                const data = {
                    year: year,
                    month: month,
                    avg_total_outpatient: avgTotalOutpatient,
                    avg_intro_outpatient: avgIntroOutpatient,
                    avg_er: avgEr,
                    avg_bed_count: avgBedCount
                };
                
                // APIリクエスト
                const result = await apiRequest('/calendar', 'POST', data);
                
                if (result) {
                    // カレンダー表示
                    displayMonthlyCalendar(result.monthly_predictions, year, month);
                    
                    // 予測データをテーブルに表示
                    const monthlyTable = document.getElementById('monthly-forecast-table').querySelector('tbody');
                    monthlyTable.innerHTML = '';
                    
                    result.monthly_predictions.forEach(item => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${item.date.replace(/-/g, '/')}</td>
                            <td>${item.day_of_week}</td>
                            <td>${item.is_holiday ? 'はい' : 'いいえ'}</td>
                            <td>${item.busyness_level}</td>
                        `;
                        monthlyTable.appendChild(row);
                    });
                    
                    // 結果を表示
                    document.getElementById('calendar-result').classList.remove('hidden');
                }
            } catch (error) {
                console.error('Calendar error:', error);
                alert(`カレンダー作成中にエラーが発生しました: ${error.message}`);
            } finally {
                showCalendarButton.disabled = false;
                showCalendarButton.textContent = 'カレンダーを表示';
            }
        });
    }
}

// タブ3: シナリオ比較の初期化
function initializeScenarioComparison() {
    // ラジオボタンの切り替え処理
    const scenarioRadios = document.querySelectorAll('input[name="scenario-type"]');
    const predefinedScenariosDiv = document.getElementById('predefined-scenarios');
    const customScenariosDiv = document.getElementById('custom-scenarios');
    
    scenarioRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'predefined') {
                predefinedScenariosDiv.classList.remove('hidden');
                customScenariosDiv.classList.add('hidden');
            } else {
                predefinedScenariosDiv.classList.add('hidden');
                customScenariosDiv.classList.remove('hidden');
                updateCustomScenarios();
            }
        });
    });
    
    // カスタムシナリオ数の変更
    const numScenariosInput = document.getElementById('num-scenarios');
    if (numScenariosInput) {
        numScenariosInput.addEventListener('change', updateCustomScenarios);
    }
    
    // 事前定義シナリオの比較ボタン
    const comparePredefinedButton = document.getElementById('compare-predefined-button');
    if (comparePredefinedButton) {
        comparePredefinedButton.addEventListener('click', async function() {
            const selectedScenarios = document.querySelectorAll('input[name="predefined-scenario"]:checked');
            
            if (selectedScenarios.length === 0) {
                alert('比較するシナリオを1つ以上選択してください');
                return;
            }
            
            try {
                comparePredefinedButton.disabled = true;
                comparePredefinedButton.textContent = '比較中...';
                
                // 事前定義シナリオを取得
                const predefinedResult = await apiRequest('/predefined_scenarios', 'GET');
                
                if (!predefinedResult || !predefinedResult.scenarios) {
                    throw new Error('事前定義シナリオを取得できませんでした');
                }
                
                // 選択されたシナリオを抽出
                const scenarios = [];
                selectedScenarios.forEach(checkbox => {
                    const scenarioId = checkbox.value;
                    const scenario = predefinedResult.scenarios.find(s => s.id === scenarioId);
                    if (scenario) {
                        scenarios.push(scenario);
                    }
                });
                
                // シナリオ比較を実行
                const result = await apiRequest('/compare', 'POST', { scenarios });
                
                if (result && result.results) {
                    displayScenarioComparison(result.results);
                }
            } catch (error) {
                console.error('Scenario comparison error:', error);
                alert(`シナリオ比較中にエラーが発生しました: ${error.message}`);
            } finally {
                comparePredefinedButton.disabled = false;
                comparePredefinedButton.textContent = 'シナリオ比較実行';
            }
        });
    }
    
    // カスタムシナリオの比較ボタン
    const compareCustomButton = document.getElementById('compare-custom-button');
    if (compareCustomButton) {
        compareCustomButton.addEventListener('click', async function() {
            const scenarioCount = parseInt(document.getElementById('num-scenarios').value);
            const scenarios = [];
            
            for (let i = 1; i <= scenarioCount; i++) {
                const scenarioName = document.getElementById(`scenario-name-${i}`).value || `シナリオ ${i}`;
                const scenarioDate = document.getElementById(`scenario-date-${i}`).value;
                const totalOutpatient = document.getElementById(`scenario-total-outpatient-${i}`).value;
                const introOutpatient = document.getElementById(`scenario-intro-outpatient-${i}`).value;
                const erCount = document.getElementById(`scenario-er-count-${i}`).value;
                const bedCount = document.getElementById(`scenario-bed-count-${i}`).value;
                
                if (!scenarioDate || !totalOutpatient || !introOutpatient || !erCount || !bedCount) {
                    alert(`シナリオ ${i} のすべての項目を入力してください`);
                    return;
                }
                
                scenarios.push({
                    name: scenarioName,
                    date: scenarioDate,
                    total_outpatient: totalOutpatient,
                    intro_outpatient: introOutpatient,
                    er_count: erCount,
                    bed_count: bedCount
                });
            }
            
            try {
                compareCustomButton.disabled = true;
                compareCustomButton.textContent = '比較中...';
                
                // シナリオ比較を実行
                const result = await apiRequest('/compare', 'POST', { scenarios });
                
                if (result && result.results) {
                    displayScenarioComparison(result.results);
                }
            } catch (error) {
                console.error('Custom scenario comparison error:', error);
                alert(`カスタムシナリオ比較中にエラーが発生しました: ${error.message}`);
            } finally {
                compareCustomButton.disabled = false;
                compareCustomButton.textContent = 'カスタムシナリオ比較実行';
            }
        });
    }
}

// タブ切り替え処理
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // アクティブなタブを非アクティブにする
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // クリックされたタブをアクティブにする
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
}

// 年の選択肢を動的に生成
function initializeYearOptions() {
    const yearSelect = document.getElementById('calendar-year');
    if (!yearSelect) return;
    
    const currentYear = new Date().getFullYear();
    
    for (let year = currentYear - 1; year <= currentYear + 2; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        
        if (year === currentYear) {
            option.selected = true;
        }
        
        yearSelect.appendChild(option);
    }
}

// モバイル表示の切り替え
function initializeMobileMode() {
    const mobileCheckbox = document.getElementById('mobile-mode');
    if (!mobileCheckbox) return;
    
    // 画面幅に基づいて初期値を設定
    const isMobile = window.innerWidth < 768;
    mobileCheckbox.checked = isMobile;
    
    if (isMobile) {
        document.body.classList.add('mobile-mode');
    }
    
    mobileCheckbox.addEventListener('change', function() {
        if (this.checked) {
            document.body.classList.add('mobile-mode');
        } else {
            document.body.classList.remove('mobile-mode');
        }
    });
}

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing app...');
    
    // タブ切り替えの初期化
    initializeTabs();
    
    // 年の選択肢を初期化
    initializeYearOptions();
    
    // モバイル表示の初期化
    initializeMobileMode();
    
    // 各タブの初期化
    initializeSinglePrediction();
    initializeMonthlyCalendar();
    initializeScenarioComparison();
    
    // 現在の月を選択
    const currentMonth = new Date().getMonth() + 1;
    if (document.getElementById('calendar-month')) {
        document.getElementById('calendar-month').value = currentMonth;
    }
    
    // カスタムシナリオの初期化
    if (document.getElementById('custom-scenarios-container')) {
        updateCustomScenarios();
    }
});
