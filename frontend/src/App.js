import React, { useState, useEffect } from 'react';
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
import { getScenarios, makePrediction, makeWeekPrediction } from './services/api';

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
  const [scenarios, setScenarios] = useState([]);
  const [loading, setLoading] = useState(false);
  const [weekLoading, setWeekLoading] = useState(false);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    // シナリオデータをロード
    const loadScenarios = async () => {
      try {
        const scenariosData = await getScenarios();
        setScenarios(scenariosData);
      } catch (err) {
        console.error('シナリオの取得に失敗しました:', err);
        setError('シナリオの取得に失敗しました。サーバーが起動しているか確認してください。');
      }
    };

    loadScenarios();
  }, []);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleSubmit = async (formData) => {
    if (tabValue === 0) {
      // 単日予測
      setLoading(true);
      setError(null);
      
      try {
        const result = await makePrediction(formData);
        setPrediction(result);
      } catch (err) {
        console.error('予測に失敗しました:', err);
        setError('予測に失敗しました。サーバーが起動しているか確認してください。');
      } finally {
        setLoading(false);
      }
    } else {
      // 週間予測
      setWeekLoading(true);
      setError(null);
      
      try {
        const result = await makeWeekPrediction(formData);
        setWeekPrediction(result);
      } catch (err) {
        console.error('週間予測に失敗しました:', err);
        setError('週間予測に失敗しました。サーバーが起動しているか確認してください。');
      } finally {
        setWeekLoading(false);
      }
    }
  };

  const handleScenarioSelect = (scenario) => {
    handleSubmit(scenario);
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
            患者情報を入力して、入院患者数を予測します。
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
              </Tabs>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Paper sx={{ p: 3, mb: 3 }} elevation={3}>
                <Typography variant="h6" gutterBottom>患者情報入力</Typography>
                <PredictionForm 
                  onSubmit={handleSubmit} 
                  loading={tabValue === 0 ? loading : weekLoading} 
                  scenarios={scenarios} 
                  onScenarioSelect={handleScenarioSelect}
                  mode={tabValue === 0 ? "day" : "week"}
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
              </Paper>
            </Box>
          </Box>
        </Box>
      </Container>
    </div>
  );
}

export default App; 