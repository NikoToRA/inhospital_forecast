// グローバル変数
const API_BASE_URL = 'http://localhost:5000/api';  // APIのベースURL

// ページの読み込み完了時の処理
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    setupTabNavigation();
    setupMobileDetection();
    
    // 各タブの初期化
    initializeSinglePrediction();
    initializeMonthlyCalendar();
    initializeScenarioComparison();
    initializeDataAnalysis();
});

// ページの初期化
function initializePage() {
    // 現在の日付を設定
    const today = new Date();
    const predictionDateInput = document.getElementById('prediction-date');
    if (predictionDateInput) {
        predictionDateInput.valueAsDate = today;
        updateDateInfo(today);
    }
    
    // カレンダー年の選択肢を動的に生成
    const calendarYearSelect = document.getElementById('calendar-year');
    if (calendarYearSelect) {
        const currentYear = today.getFullYear();
        for (let year = currentYear - 1; year <= currentYear + 2; year++) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            if (year === currentYear) {
                option.selected = true;
            }
            calendarYearSelect.appendChild(option);
        }
    }
    
    // 現在の月を選択
    const calendarMonthSelect = document.getElementById('calendar-month');
    if (calendarMonthSelect) {
        calendarMonthSelect.value = today.getMonth() + 1;
    }
}

// タブ切り替え機能の設定
function setupTabNavigation() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // アクティブなタブを非アクティブにする
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // クリックされたタブをアクティブにする
            button.classList.add('active');
            const targetTab = button.getAttribute('data-tab');
            document.getElementById(targetTab).classList.add('active');
        });
    });
}

// モバイル検出機能の設定
function setupMobileDetection() {
    const mobileCheckbox = document.getElementById('mobile-mode');
    
    // 画面幅に基づいてモバイルモードを設定
    function detectMobileDevice() {
        const isMobile = window.innerWidth < 768;
        if (mobileCheckbox) {
            mobileCheckbox.checked = isMobile;
            document.body.classList.toggle('mobile-view', isMobile);
        }
    }
    
    // 初期検出
    detectMobileDevice();
    
    // 画面サイズ変更時に再検出
    window.addEventListener('resize', detectMobileDevice);
    
    // チェックボックスの切り替え時の処理
    if (mobileCheckbox) {
        mobileCheckbox.addEventListener('change', function() {
            document.body.classList.toggle('mobile-view', this.checked);
        });
    }
}

// APIリクエスト用のヘルパー関数
async function apiRequest(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        
        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request error:', error);
        alert(`エラーが発生しました: ${error.message}`);
        return null;
    }
}

// 日付情報の更新
function updateDateInfo(dateObj) {
    const dateInfo = document.getElementById('date-info');
    if (!dateInfo) return;
    
    // 曜日の取得
    const weekdays = ['日曜日', '月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日'];
    const dayOfWeek = weekdays[dateObj.getDay()];
    
    // 日付のフォーマット
    const year = dateObj.getFullYear();
    const month = dateObj.getMonth() + 1;
    const day = dateObj.getDate();
    
    // 祝日かどうかの判定は一旦無しで表示（後でAPIから取得）
    dateInfo.innerHTML = `<strong>${year}年${month}月${day}日（${dayOfWeek}）</strong>`;
}

// モック予測として単純なランダム値を返す関数（サーバーがない場合の仮実装）
function mockPredict() {
    // 実際はサーバーサイドで計算するが、ここではシンプルなダミー計算
    // 曜日係数（月曜が高く、週末が低い）
    const baseValue = 50 + Math.random() * 20;
    return baseValue;
}

// 以下で各タブの機能を実装するための関数を宣言
// 実際の実装はimports.jsファイルで行う

// タブ1: 単一予測の初期化
function initializeSinglePrediction() {
    const predictionDateInput = document.getElementById('prediction-date');
    const predictButton = document.getElementById('predict-button');
    const savePredictionButton = document.getElementById('save-prediction-button');
    const confirmSaveButton = document.getElementById('confirm-save-button');
    
    if (predictionDateInput) {
        predictionDateInput.addEventListener('change', function() {
            updateDateInfo(this.valueAsDate);
        });
    }
    
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
            
            // 予測リクエスト
            try {
                // 予測データを非表示にして、ローディング表示
                document.getElementById('prediction-result').classList.add('hidden');
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
                    // 予測結果を表示
                    document.getElementById('prediction-value').textContent = result.prediction.toFixed(1);
                    
                    // 日付情報を更新（祝日情報含む）
                    const dateInfo = document.getElementById('date-info');
                    if (dateInfo) {
                        let dateText = `<strong>${date.replace(/-/g, '/')} (${result.date_info.day_of_week})</strong>`;
                        if (result.date_info.is_holiday) {
                            dateText += `<div class="holiday-badge">祝日: ${result.date_info.holiday_name || '休日'}</div>`;
                        }
                        dateInfo.innerHTML = dateText;
                    }
                    
                    // 週間予測データをテーブルに表示
                    const weeklyTable = document.getElementById('weekly-forecast-table').querySelector('tbody');
                    weeklyTable.innerHTML = '';
                    
                    result.weekly_forecast.forEach(item => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${item.date.replace(/-/g, '/')}</td>
                            <td>${item.day_of_week}</td>
                            <td>${item.predicted_admission.toFixed(1)}</td>
                        `;
                        weeklyTable.appendChild(row);
                    });
                    
                    // グラフ表示
                    displayWeeklyChart(result.weekly_forecast);
                    
                    // 予測結果を表示
                    document.getElementById('prediction-result').classList.remove('hidden');
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
    
    // 保存ボタンの処理
    if (savePredictionButton) {
        savePredictionButton.addEventListener('click', function() {
            const saveForm = document.getElementById('save-form');
            saveForm.classList.toggle('hidden');
            
            // 予測値を実際の入院患者数初期値として設定
            const predictionValue = document.getElementById('prediction-value').textContent;
            document.getElementById('real-admission').value = predictionValue;
        });
    }
    
    // 確定して保存ボタンの処理
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
                
                const date = document.getElementById('prediction-date').value;
                const dateObj = new Date(date);
                const weekdays = ['日曜日', '月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日'];
                const dayOfWeek = weekdays[dateObj.getDay()];
                
                const data = {
                    date: date,
                    day_of_week: dayOfWeek,
                    total_outpatient: document.getElementById('total-outpatient').value,
                    intro_outpatient: document.getElementById('intro-outpatient').value,
                    er_count: document.getElementById('er-count').value,
                    bed_count: document.getElementById('bed-count').value,
                    actual_admission: realAdmission
                };
                
                // APIリクエスト
                const result = await apiRequest('/save', 'POST', data);
                
                if (result && result.success) {
                    alert(result.message);
                    document.getElementById('save-form').classList.add('hidden');
                    
                    // データ分析タブのデータを更新
                    initializeDataAnalysis();
                }
            } catch (error) {
                console.error('Save error:', error);
                alert(`データ保存中にエラーが発生しました: ${error.message}`);
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

// 月間カレンダーの表示
function displayMonthlyCalendar(monthlyData, year, month) {
    const calendarContainer = document.getElementById('monthly-calendar');
    if (!calendarContainer) return;
    
    // カレンダーのテーブルを作成
    const table = document.createElement('table');
    table.className = 'calendar-table';
    
    // ヘッダー（曜日）
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    const weekdays = ['日', '月', '火', '水', '木', '金', '土'];
    
    weekdays.forEach(day => {
        const th = document.createElement('th');
        th.textContent = day;
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // 本体（日付）
    const tbody = document.createElement('tbody');
    
    // 月の最初の日の曜日を取得
    const firstDay = new Date(year, month - 1, 1).getDay();
    
    // 月の最終日を取得
    const lastDate = new Date(year, month, 0).getDate();
    
    // 週の行を作成
    let date = 1;
    for (let i = 0; i < 6; i++) {
        // 6週分のカレンダーを用意（必要に応じて表示）
        if (date > lastDate) break;
        
        const row = document.createElement('tr');
        
        // 各曜日のセルを作成
        for (let j = 0; j < 7; j++) {
            const cell = document.createElement('td');
            cell.className = 'calendar-day';
            
            // 最初の週の空白セル
            if (i === 0 && j < firstDay) {
                row.appendChild(cell);
                continue;
            }
            
            // 月末以降の空白セル
            if (date > lastDate) {
                row.appendChild(cell);
                continue;
            }
            
            // 該当日のデータを取得
            const dayData = monthlyData.find(item => {
                const itemDate = new Date(item.date);
                return itemDate.getDate() === date;
            });
            
            if (dayData) {
                // 日付表示
                const dayNumber = document.createElement('div');
                dayNumber.className = 'day-number';
                dayNumber.textContent = date;
                
                // 祝日表示
                if (dayData.is_holiday) {
                    dayNumber.style.color = '#c62828';
                    
                    if (dayData.holiday_name) {
                        const holidayName = document.createElement('div');
                        holidayName.className = 'holiday-name';
                        holidayName.textContent = dayData.holiday_name;
                        holidayName.style.fontSize = '0.8em';
                        cell.appendChild(holidayName);
                    }
                }
                
                // 予測患者数表示
                const prediction = document.createElement('div');
                prediction.className = 'prediction';
                prediction.textContent = `${dayData.predicted_admission.toFixed(1)} 人`;
                prediction.style.fontWeight = 'bold';
                
                // 混雑度に応じた背景色
                cell.style.backgroundColor = dayData.busyness_color;
                
                // 混雑度表示
                const busyness = document.createElement('div');
                busyness.className = 'busyness';
                busyness.textContent = dayData.busyness_level;
                busyness.style.fontSize = '0.8em';
                
                cell.appendChild(dayNumber);
                cell.appendChild(prediction);
                cell.appendChild(busyness);
            }
            
            row.appendChild(cell);
            date++;
        }
        
        tbody.appendChild(row);
    }
    
    table.appendChild(tbody);
    
    // カレンダーを表示
    calendarContainer.innerHTML = '';
    calendarContainer.appendChild(table);
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

// カスタムシナリオフォームの更新
function updateCustomScenarios() {
    const container = document.getElementById('custom-scenarios-container');
    const count = parseInt(document.getElementById('num-scenarios').value);
    
    if (!container) return;
    
    // コンテナをクリア
    container.innerHTML = '';
    
    // 現在の日付
    const today = new Date();
    
    // 各シナリオのフォームを生成
    for (let i = 1; i <= count; i++) {
        const scenarioDiv = document.createElement('div');
        scenarioDiv.className = 'scenario-form';
        scenarioDiv.innerHTML = `
            <h4>シナリオ ${i}</h4>
            <div class="form-row">
                <div class="form-column">
                    <div class="form-group">
                        <label for="scenario-name-${i}">シナリオ名</label>
                        <input type="text" id="scenario-name-${i}" class="form-control" placeholder="シナリオ ${i}">
                    </div>
                    <div class="form-group">
                        <label for="scenario-date-${i}">日付</label>
                        <input type="date" id="scenario-date-${i}" class="form-control" value="${today.toISOString().split('T')[0]}">
                    </div>
                    <div id="scenario-day-${i}" class="date-info"></div>
                </div>
                <div class="form-column">
                    <div class="form-group">
                        <label for="scenario-total-outpatient-${i}">前日総外来患者数</label>
                        <input type="number" id="scenario-total-outpatient-${i}" class="form-control" min="0" max="2000" value="500">
                    </div>
                    <div class="form-group">
                        <label for="scenario-intro-outpatient-${i}">前日紹介外来患者数</label>
                        <input type="number" id="scenario-intro-outpatient-${i}" class="form-control" min="0" max="200" value="20">
                    </div>
                    <div class="form-group">
                        <label for="scenario-er-count-${i}">前日救急搬送患者数</label>
                        <input type="number" id="scenario-er-count-${i}" class="form-control" min="0" max="100" value="15">
                    </div>
                    <div class="form-group">
                        <label for="scenario-bed-count-${i}">現在の病床利用数</label>
                        <input type="number" id="scenario-bed-count-${i}" class="form-control" min="100" max="1000" value="280">
                    </div>
                </div>
            </div>
            <div class="divider"></div>
        `;
        
        container.appendChild(scenarioDiv);
        
        // 日付選択時のイベントリスナーを設定
        const dateInput = document.getElementById(`scenario-date-${i}`);
        if (dateInput) {
            // 初期日付情報を更新
            const initialDate = new Date(dateInput.value);
            updateScenarioDateInfo(i, initialDate);
            
            // 日付変更時のイベント
            dateInput.addEventListener('change', function() {
                updateScenarioDateInfo(i, new Date(this.value));
            });
        }
    }
}

// シナリオの日付情報を更新
function updateScenarioDateInfo(scenarioIndex, dateObj) {
    const dateInfo = document.getElementById(`scenario-day-${scenarioIndex}`);
    if (!dateInfo) return;
    
    // 曜日の取得
    const weekdays = ['日曜日', '月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日'];
    const dayOfWeek = weekdays[dateObj.getDay()];
    
    dateInfo.textContent = `選択日の曜日: ${dayOfWeek}`;
}

// タブ4: データ分析の初期化
function initializeDataAnalysis() {
    loadDataAnalysis();
}

// データ分析の読み込み
async function loadDataAnalysis() {
    try {
        const result = await apiRequest('/data', 'GET');
        
        if (result) {
            // サンプルデータ表示
            displayDataSample(result.sample);
            
            // 基本統計量表示
            displayDataStats(result.stats);
            
            // グラフ表示
            displayTimeSeriesChart(result.time_series);
            displayDayOfWeekChart(result.day_means);
            displayScatterChart(result.scatter_data);
        }
    } catch (error) {
        console.error('Data analysis error:', error);
        alert(`データ分析中にエラーが発生しました: ${error.message}`);
    }
}

// シナリオ比較結果の表示
function displayScenarioComparison(results) {
    // テーブルにデータを表示
    const tableBody = document.getElementById('scenario-comparison-table').querySelector('tbody');
    tableBody.innerHTML = '';
    
    results.forEach(result => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${result.name}</td>
            <td>${result.date.replace(/-/g, '/')}</td>
            <td>${result.day_of_week}</td>
            <td>${result.predicted_admission.toFixed(1)}</td>
        `;
        tableBody.appendChild(row);
    });
    
    // グラフ表示
    const ctx = document.getElementById('comparison-chart-canvas').getContext('2d');
    
    // 既存のチャートを破棄
    if (window.comparisonChart) {
        window.comparisonChart.destroy();
    }
    
    // データ準備
    const labels = results.map(item => item.name);
    const data = results.map(item => item.predicted_admission);
    
    // 色の生成
    const colors = generateColors(results.length);
    
    // チャート作成
    window.comparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '予測入院患者数',
                data: data,
                backgroundColor: colors.map(color => `rgba(${color.r}, ${color.g}, ${color.b}, 0.7)`),
                borderColor: colors.map(color => `rgba(${color.r}, ${color.g}, ${color.b}, 1)`),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'シナリオ別予測入院患者数比較',
                    font: {
                        size: 18,
                        weight: 'bold'
                    },
                    padding: 20
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `入院患者数: ${context.parsed.y.toFixed(1)}人`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: '予測入院患者数',
                        font: {
                            weight: 'bold'
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'シナリオ',
                        font: {
                            weight: 'bold'
                        }
                    }
                }
            }
        }
    });
    
    // 比較結果を表示
    document.getElementById('scenario-comparison-result').classList.remove('hidden');
}

// データサンプルの表示
function displayDataSample(sampleData) {
    const table = document.getElementById('data-sample-table');
    if (!table || sampleData.length === 0) return;
    
    table.innerHTML = '';
    
    // ヘッダー
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    Object.keys(sampleData[0]).forEach(key => {
        const th = document.createElement('th');
        th.textContent = key;
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // データ行
    const tbody = document.createElement('tbody');
    
    sampleData.forEach(item => {
        const row = document.createElement('tr');
        
        Object.values(item).forEach(value => {
            const td = document.createElement('td');
            td.textContent = value;
            row.appendChild(td);
        });
        
        tbody.appendChild(row);
    });
    
    table.appendChild(tbody);
}

// 統計データの表示
function displayDataStats(statsData) {
    const table = document.getElementById('data-stats-table');
    if (!table || statsData.length === 0) return;
    
    table.innerHTML = '';
    
    // ヘッダー
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    Object.keys(statsData[0]).forEach(key => {
        const th = document.createElement('th');
        th.textContent = key;
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // データ行
    const tbody = document.createElement('tbody');
    
    statsData.forEach(item => {
        const row = document.createElement('tr');
        
        Object.values(item).forEach(value => {
            const td = document.createElement('td');
            
            // 数値の場合は小数点以下2桁に
            if (typeof value === 'number') {
                td.textContent = value.toFixed(2);
            } else {
                td.textContent = value;
            }
            
            row.appendChild(td);
        });
        
        tbody.appendChild(row);
    });
    
    table.appendChild(tbody);
}

// 時系列チャートの表示
function displayTimeSeriesChart(timeData) {
    const ctx = document.getElementById('time-series-chart').getContext('2d');
    
    // 既存のチャートを破棄
    if (window.timeSeriesChart) {
        window.timeSeriesChart.destroy();
    }
    
    // データ準備
    const labels = timeData.map(item => item.date);
    const data = timeData.map(item => item.value);
    
    // チャート作成
    window.timeSeriesChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '入院患者数',
                data: data,
                backgroundColor: 'rgba(0, 70, 127, 0.2)',
                borderColor: 'rgba(0, 70, 127, 1)',
                borderWidth: 1,
                pointRadius: 2,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '入院患者数の推移',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'month',
                        displayFormats: {
                            month: 'yyyy/MM'
                        }
                    },
                    title: {
                        display: true,
                        text: '日付'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '入院患者数'
                    }
                }
            }
        }
    });
}

// 曜日別平均入院患者数チャートの表示
function displayDayOfWeekChart(dayData) {
    const ctx = document.getElementById('day-of-week-chart').getContext('2d');
    
    // 既存のチャートを破棄
    if (window.dayOfWeekChart) {
        window.dayOfWeekChart.destroy();
    }
    
    // データ準備
    const labels = dayData.map(item => item.day);
    const data = dayData.map(item => item.mean);
    
    // 曜日ごとの色（月〜日）
    const colors = [
        {r: 65, g: 105, b: 225},  // 月: ロイヤルブルー
        {r: 46, g: 139, b: 87},   // 火: シーグリーン
        {r: 255, g: 165, b: 0},   // 水: オレンジ
        {r: 106, g: 90, b: 205},  // 木: スレートブルー
        {r: 60, g: 179, b: 113},  // 金: ミディアムシーグリーン
        {r: 30, g: 144, b: 255},  // 土: ドジャーブルー
        {r: 178, g: 34, b: 34}    // 日: 濃い赤
    ];
    
    // チャート作成
    window.dayOfWeekChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '平均入院患者数',
                data: data,
                backgroundColor: colors.map(color => `rgba(${color.r}, ${color.g}, ${color.b}, 0.7)`),
                borderColor: colors.map(color => `rgba(${color.r}, ${color.g}, ${color.b}, 1)`),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '曜日別の平均入院患者数',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '平均入院患者数'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '曜日'
                    }
                }
            }
        }
    });
}

// 散布図の表示（外来患者数 vs 入院患者数）
function displayScatterChart(scatterData) {
    const ctx = document.getElementById('scatter-chart').getContext('2d');
    
    // 既存のチャートを破棄
    if (window.scatterChart) {
        window.scatterChart.destroy();
    }
    
    // チャート作成
    window.scatterChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: '入院患者数 vs 外来患者数',
                data: scatterData,
                backgroundColor: 'rgba(0, 70, 127, 0.7)',
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '外来患者数と入院患者数の関係',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '外来患者数'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '入院患者数'
                    }
                }
            }
        }
    });
}

// 色生成のヘルパー関数
function generateColors(count) {
    const baseColors = [
        {r: 65, g: 105, b: 225},  // ロイヤルブルー
        {r: 46, g: 139, b: 87},   // シーグリーン
        {r: 255, g: 165, b: 0},   // オレンジ
        {r: 106, g: 90, b: 205},  // スレートブルー
        {r: 60, g: 179, b: 113},  // ミディアムシーグリーン
        {r: 30, g: 144, b: 255},  // ドジャーブルー
        {r: 178, g: 34, b: 34},   // 濃い赤
        {r: 148, g: 0, b: 211},   // ダークバイオレット
        {r: 0, g: 128, b: 128},   // ティール
        {r: 220, g: 20, b: 60}    // クリムゾン
    ];
    
    // 必要な数だけ色を生成
    const colors = [];
    for (let i = 0; i < count; i++) {
        if (i < baseColors.length) {
            colors.push(baseColors[i]);
        } else {
            // 基本色が足りない場合はランダムに生成
            colors.push({
                r: Math.floor(Math.random() * 200) + 20,
                g: Math.floor(Math.random() * 200) + 20,
                b: Math.floor(Math.random() * 200) + 20
            });
        }
    }
    
    return colors;
}

// 週間予測グラフの表示
function displayWeeklyChart(weeklyData) {
    const ctx = document.getElementById('weekly-chart-canvas').getContext('2d');
    
    // 既存のチャートを破棄
    if (window.weeklyChart) {
        window.weeklyChart.destroy();
    }
    
    // データ準備
    const labels = weeklyData.map(item => {
        const date = new Date(item.date);
        return `${date.getMonth() + 1}/${date.getDate()}`;
    });
    
    const data = weeklyData.map(item => item.predicted_admission);
    
    // チャート作成
    window.weeklyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '予測入院患者数',
                data: data,
                backgroundColor: 'rgba(0, 70, 127, 0.2)',
                borderColor: 'rgba(0, 70, 127, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(0, 70, 127, 1)',
                pointRadius: 5,
                pointHoverRadius: 7,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '今後1週間の入院患者数予測',
                    font: {
                        size: 18,
                        weight: 'bold'
                    },
                    padding: 20
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `入院患者数: ${context.parsed.y.toFixed(1)}人`;
                        },
                        title: function(tooltipItems) {
                            const index = tooltipItems[0].dataIndex;
                            return `${labels[index]} (${weeklyData[index].day_of_week})`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: '予測入院患者数',
                        font: {
                            weight: 'bold'
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '日付',
                        font: {
                            weight: 'bold'
                        }
                    }
                }
            }
        }
    });
}

// 共通関数や他のタブの処理はapp.jsの続きのファイルに記述します 