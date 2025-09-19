-- 病院内予測システム用テーブル

-- 予測ログテーブル
CREATE TABLE prediction_logs (
    id BIGSERIAL PRIMARY KEY,
    prediction_date DATE NOT NULL,
    predicted_value FLOAT NOT NULL,
    total_outpatient INTEGER,
    intro_outpatient INTEGER,
    er_patients INTEGER,
    bed_count INTEGER,
    public_holiday BOOLEAN DEFAULT FALSE,
    day_of_week VARCHAR(10),
    features JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- シナリオデータキャッシュテーブル
CREATE TABLE scenario_cache (
    id BIGSERIAL PRIMARY KEY,
    data_hash VARCHAR(64) UNIQUE,
    scenario_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- アプリケーション設定テーブル
CREATE TABLE app_settings (
    id BIGSERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス作成
CREATE INDEX idx_prediction_logs_date ON prediction_logs(prediction_date);
CREATE INDEX idx_prediction_logs_created_at ON prediction_logs(created_at);
CREATE INDEX idx_app_settings_key ON app_settings(setting_key);

-- Row Level Security (RLS) 有効化
ALTER TABLE prediction_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scenario_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_settings ENABLE ROW LEVEL SECURITY;

-- パブリックアクセス許可（開発用）
CREATE POLICY "Public read access" ON prediction_logs FOR SELECT USING (true);
CREATE POLICY "Public insert access" ON prediction_logs FOR INSERT WITH CHECK (true);

CREATE POLICY "Public read access" ON scenario_cache FOR SELECT USING (true);
CREATE POLICY "Public insert access" ON scenario_cache FOR INSERT WITH CHECK (true);
CREATE POLICY "Public update access" ON scenario_cache FOR UPDATE USING (true);

CREATE POLICY "Public read access" ON app_settings FOR SELECT USING (true);
CREATE POLICY "Public insert access" ON app_settings FOR INSERT WITH CHECK (true);
CREATE POLICY "Public update access" ON app_settings FOR UPDATE USING (true);

-- 初期設定データ挿入
INSERT INTO app_settings (setting_key, setting_value, description) VALUES
('model_version', '1.0.0', 'Current ML model version'),
('last_model_update', NOW()::TEXT, 'Last time model was updated'),
('api_version', '1.0.0', 'API version');