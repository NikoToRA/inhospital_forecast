import React from 'react';
import {
  TextField,
  Button,
  Grid,
  Typography,
  Box,
  Alert,
  CircularProgress
} from '@mui/material';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import DateRangeIcon from '@mui/icons-material/DateRange';

// 今日の日付をYYYY-MM-DD形式で取得する関数
const getTodayFormatted = () => {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const PredictionForm = ({ onSubmit, loading, mode = "day", formData, onChange }) => {

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    // 数値フィールドの場合は整数に変換
    if (type === 'number') {
      onChange({ [name]: parseInt(value, 10) || 0 });
    } else if (type === 'checkbox') {
      onChange({ [name]: checked });
    } else {
      onChange({ [name]: value });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // モードに応じたデータを送信（祝日は自動判定）
    if (mode === 'day') {
      onSubmit({
        date: formData.target_date,
        total_outpatient: formData.total_outpatient,
        intro_outpatient: formData.intro_outpatient,
        ER: formData.er,
        bed_count: formData.bed_count
      });
    } else {
      onSubmit({
        start_date: formData.start_date,
        total_outpatient: formData.total_outpatient,
        intro_outpatient: formData.intro_outpatient,
        ER: formData.er,
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
          前日の外来患者数、救急患者数、現在の病床数などの病院情報から予測します。
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
            variant="outlined"
            InputLabelProps={{
              shrink: true,
            }}
          />
        </Grid>
        
        
        <Grid item xs={12}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            前日の病院状況
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
      
      {/* シナリオ選択は不要のため削除 */}
    </form>
  );
};

export default PredictionForm; 
