import React, { useEffect, useState } from 'react';
import { 
  Container, 
  Typography, 
  AppBar, 
  Toolbar, 
  Box, 
  Paper,
  Tab,
  Tabs
} from '@mui/material';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import PredictionForm from './components/PredictionForm';
import PredictionResult from './components/PredictionResult';
import WeekPrediction from './components/WeekPrediction';
import CalendarPrediction from './components/CalendarPrediction';
import { makePrediction, makeWeekPrediction, makeMonthPrediction } from './services/api';

// タブパネルのコンポーネント
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function App() {
  const [prediction, setPrediction] = useState(null);
  const [weekPrediction, setWeekPrediction] = useState(null);
  const [monthCur, setMonthCur] = useState(null);
  const [monthNext, setMonthNext] = useState(null);
  const [loading, setLoading] = useState(false);
  const [weekLoading, setWeekLoading] = useState(false);
  const [monthLoading, setMonthLoading] = useState(false);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const today = new Date();
  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, '0');
  const dd = String(today.getDate()).padStart(2, '0');
  const nextMonth = new Date(today.getFullYear(), today.getMonth() + 1, 1);

  const [formData, setFormData] = useState({
    target_date: `${yyyy}-${mm}-${dd}`,
    start_date: `${yyyy}-${mm}-${dd}`,
    total_outpatient: 500,
    intro_outpatient: 20,
    er: 15,
    bed_count: 280,
  });

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // 初回にカレンダーを更新（定義後に呼ぶ）

  const handleFormChange = (patch) => {
    setFormData((prev) => ({ ...prev, ...patch }));
  };

  const refreshCalendar = async (base) => {
    try {
      setMonthLoading(true);
      const cur = await makeMonthPrediction({
        year: today.getFullYear(),
        month: today.getMonth() + 1,
        total_outpatient: base.total_outpatient,
        intro_outpatient: base.intro_outpatient,
        ER: base.er,
        bed_count: base.bed_count,
      });
      const nxt = await makeMonthPrediction({
        year: nextMonth.getFullYear(),
        month: nextMonth.getMonth() + 1,
        total_outpatient: base.total_outpatient,
        intro_outpatient: base.intro_outpatient,
        ER: base.er,
        bed_count: base.bed_count,
      });
      setMonthCur(cur);
      setMonthNext(nxt);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error('月間予測取得に失敗:', e);
    } finally {
      setMonthLoading(false);
    }
  };

  // 初回マウント時に月間カレンダーを取得
  useEffect(() => {
    refreshCalendar(formData);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = async (payloadFromForm) => {
    const base = { ...formData, ...payloadFromForm };
    if (tabValue === 0) {
      // 単日予測
      setLoading(true);
      setError(null);
      
      try {
        const result = await makePrediction({
          date: base.target_date,
          total_outpatient: base.total_outpatient,
          intro_outpatient: base.intro_outpatient,
          ER: base.er,
          bed_count: base.bed_count,
        });
        setPrediction(result);
      } catch (err) {
        console.error('予測に失敗しました:', err);
        console.error('予測エラーの詳細:', {
          message: err.message,
          response: err.response?.data,
          status: err.response?.status,
          url: err.config?.url,
          formData: base
        });
        setError(`予測に失敗しました。詳細: ${err.message} (フォームデータ: ${JSON.stringify(base)})`);
      } finally {
        setLoading(false);
      }
    } else {
      // 週間予測
      setWeekLoading(true);
      setError(null);
      
      try {
        const result = await makeWeekPrediction({
          start_date: base.start_date,
          total_outpatient: base.total_outpatient,
          intro_outpatient: base.intro_outpatient,
          ER: base.er,
          bed_count: base.bed_count,
        });
        setWeekPrediction(result);
      } catch (err) {
        console.error('週間予測に失敗しました:', err);
        setError('週間予測に失敗しました。サーバーが起動しているか確認してください。');
      } finally {
        setWeekLoading(false);
      }
    }

    // カレンダーも最新入力で更新
    refreshCalendar(base);
  };

  return (
    <div>
      <AppBar position="static">
        <Toolbar>
          <LocalHospitalIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            入院患者数予測システム
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Container maxWidth="lg">
        <Box sx={{ mt: 4, mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            入院患者数予測
          </Typography>
          <Typography variant="body1" paragraph>
            病院情報を1箇所に入力し、翌日・週間・月間カレンダーのすべてに反映します。
          </Typography>
          
          {error && (
            <Paper sx={{ p: 2, mb: 2, bgcolor: '#ffebee' }} elevation={0}>
              <Typography color="error">{error}</Typography>
            </Paper>
          )}
          
          <Box sx={{ width: '100%' }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
              <Tabs value={tabValue} onChange={handleTabChange} aria-label="予測モード選択">
                <Tab label="翌日予測" id="tab-0" />
                <Tab label="週間予測" id="tab-1" />
                <Tab label="月間カレンダー" id="tab-2" />
              </Tabs>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Paper sx={{ p: 3, mb: 3 }} elevation={3}>
                <Typography variant="h6" gutterBottom>病院情報入力</Typography>
                <PredictionForm
                  onSubmit={handleSubmit}
                  loading={tabValue === 0 ? loading : weekLoading}
                  mode={tabValue === 0 ? "day" : "week"}
                  formData={formData}
                  onChange={handleFormChange}
                />
              </Paper>
            </Box>
            
            <Box sx={{ flex: 1 }}>
              <Paper sx={{ p: 3, mb: 3, height: '100%' }} elevation={3}>
                <TabPanel value={tabValue} index={0}>
                  <Typography variant="h6" gutterBottom>翌日予測結果</Typography>
                  <PredictionResult prediction={prediction} loading={loading} />
                </TabPanel>
                <TabPanel value={tabValue} index={1}>
                  <Typography variant="h6" gutterBottom>週間予測結果</Typography>
                  <WeekPrediction weekPrediction={weekPrediction} loading={weekLoading} />
                </TabPanel>
                <TabPanel value={tabValue} index={2}>
                  <Typography variant="h6" gutterBottom>月間カレンダー表示（今月と来月）</Typography>
                  <CalendarPrediction
                    inputs={formData}
                    monthCur={monthCur}
                    monthNext={monthNext}
                    loading={monthLoading}
                  />
                </TabPanel>
              </Paper>
            </Box>
          </Box>
        </Box>
      </Container>
    </div>
  );
}

export default App; 
