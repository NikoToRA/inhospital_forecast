import React, { useState } from 'react';
import {
  TextField,
  Button,
  Grid,
  FormControlLabel,
  Switch,
  Typography,
  Box,
  Divider,
  Chip,
  Alert,
  CircularProgress
} from '@mui/material';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import DateRangeIcon from '@mui/icons-material/DateRange';

const PredictionForm = ({ onSubmit, loading, scenarios, onScenarioSelect, mode = "day" }) => {
  const today = new Date();
  const formattedToday = today.toISOString().split('T')[0]; // YYYY-MM-DD形式
  
  const [formData, setFormData] = useState({
    target_date: formattedToday,
    start_date: formattedToday,
    public_holiday: false,
    public_holiday_previous_day: false,
    total_outpatient: 500,
    intro_outpatient: 20,
    er: 15,
    bed_count: 280
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    // 数値フィールドの場合は整数に変換
    if (type === 'number') {
      setFormData({
        ...formData,
        [name]: parseInt(value, 10) || 0
      });
    } else if (type === 'checkbox') {
      setFormData({
        ...formData,
        [name]: checked
      });
    } else {
      setFormData({
        ...formData,
        [name]: value
      });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // モードに応じたデータを送信
    if (mode === 'day') {
      onSubmit({
        target_date: formData.target_date,
        public_holiday: formData.public_holiday,
        public_holiday_previous_day: formData.public_holiday_previous_day,
        total_outpatient: formData.total_outpatient,
        intro_outpatient: formData.intro_outpatient,
        er: formData.er,
        bed_count: formData.bed_count
      });
    } else {
      onSubmit({
        start_date: formData.start_date,
        public_holiday: formData.public_holiday,
        public_holiday_previous_day: formData.public_holiday_previous_day,
        total_outpatient: formData.total_outpatient,
        intro_outpatient: formData.intro_outpatient,
        er: formData.er,
        bed_count: formData.bed_count
      });
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {mode === "week" ? (
        <Alert severity="info" sx={{ mb: 2 }}>
          開始日から7日間の入院患者数予測を行います。曜日は自動で計算されます。
          土日祝日は外来患者数を自動調整します。
        </Alert>
      ) : (
        <Alert severity="info" sx={{ mb: 2 }}>
          指定した日付の入院患者数を予測します。
          前日の外来患者数、救急患者数、現在の病床数から予測します。
        </Alert>
      )}
      
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label={mode === "day" ? "予測日" : "予測開始日"}
            type="date"
            name={mode === "day" ? "target_date" : "start_date"}
            value={mode === "day" ? formData.target_date : formData.start_date}
            onChange={handleChange}
            InputLabelProps={{
              shrink: true,
            }}
          />
        </Grid>
        
        <Grid item xs={12} sm={6}>
          <FormControlLabel
            control={
              <Switch
                checked={formData.public_holiday}
                onChange={handleChange}
                name="public_holiday"
              />
            }
            label="祝日"
          />
        </Grid>
        
        <Grid item xs={12} sm={6}>
          <FormControlLabel
            control={
              <Switch
                checked={formData.public_holiday_previous_day}
                onChange={handleChange}
                name="public_holiday_previous_day"
              />
            }
            label="前日が祝日"
          />
        </Grid>
        
        <Grid item xs={12}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            前日の患者情報
          </Typography>
        </Grid>
        
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="前日の総外来患者数"
            name="total_outpatient"
            type="number"
            value={formData.total_outpatient}
            onChange={handleChange}
            variant="outlined"
            InputProps={{ inputProps: { min: 0 } }}
          />
        </Grid>
        
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="前日の紹介外来患者数"
            name="intro_outpatient"
            type="number"
            value={formData.intro_outpatient}
            onChange={handleChange}
            variant="outlined"
            InputProps={{ inputProps: { min: 0 } }}
          />
        </Grid>
        
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="前日の救急患者数"
            name="er"
            type="number"
            value={formData.er}
            onChange={handleChange}
            variant="outlined"
            InputProps={{ inputProps: { min: 0 } }}
          />
        </Grid>
        
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="現在の病床数"
            name="bed_count"
            type="number"
            value={formData.bed_count}
            onChange={handleChange}
            variant="outlined"
            InputProps={{ inputProps: { min: 0 } }}
          />
        </Grid>
        
        <Grid item xs={12}>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            sx={{ mt: 1 }}
            startIcon={mode === "day" ? <CalendarMonthIcon /> : <DateRangeIcon />}
            disabled={loading}
          >
            {loading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              mode === "day" ? "翌日予測を実行" : "週間予測を実行"
            )}
          </Button>
        </Grid>
      </Grid>
      
      {scenarios && scenarios.length > 0 && (
        <Box sx={{ mt: 4 }}>
          <Divider>
            <Chip label="シナリオ選択" />
          </Divider>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
            あらかじめ用意されたシナリオから選択することもできます。
          </Typography>
          <Grid container spacing={1}>
            {scenarios.map((scenario, index) => (
              <Grid item xs={12} key={index}>
                <Button
                  variant="outlined"
                  size="small"
                  fullWidth
                  onClick={() => onScenarioSelect(scenario)}
                  sx={{ justifyContent: 'flex-start', textAlign: 'left' }}
                >
                  {scenario.name}
                </Button>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
    </form>
  );
};

export default PredictionForm; 