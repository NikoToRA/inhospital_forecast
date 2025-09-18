import React from 'react';
import { Box, Typography, CircularProgress, Paper, Divider, Chip } from '@mui/material';
import BedIcon from '@mui/icons-material/Bed';
import EventIcon from '@mui/icons-material/Event';
import WbSunnyIcon from '@mui/icons-material/WbSunny';
import AcUnitIcon from '@mui/icons-material/AcUnit';
import FilterDramaIcon from '@mui/icons-material/FilterDrama';
import NatureIcon from '@mui/icons-material/Nature';

const PredictionResult = ({ prediction, loading }) => {
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!prediction) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
        <Typography variant="body1" color="text.secondary">
          予測を実行すると、結果がここに表示されます。
        </Typography>
      </Box>
    );
  }

  const { prediction: predictedValue, features, target_date, day_of_week, day_name, season } = prediction;
  
  // 予測値の調整は不要になりました
  // const adjustedPrediction = Math.round(predictedValue * 8.22 * 10) / 10;
  
  // 季節に対応するアイコンを取得
  const getSeasonIcon = (season) => {
    switch (season) {
      case 'spring':
        return <NatureIcon />;
      case 'summer':
        return <WbSunnyIcon />;
      case 'autumn':
        return <FilterDramaIcon />;
      case 'winter':
        return <AcUnitIcon />;
      default:
        return null;
    }
  };
  
  // 季節の日本語名を取得
  const getSeasonName = (season) => {
    const seasonMap = {
      'spring': '春',
      'summer': '夏',
      'autumn': '秋',
      'winter': '冬'
    };
    return seasonMap[season] || '不明';
  };
  
  const isHoliday = features.public_holiday === 1;
  const isPrevHoliday = features.public_holiday_previous_day === 1;
  
  // 日付のフォーマット変更（YYYY-MM-DDからYYYY/MM/DDへ）
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    return dateStr.replace(/-/g, '/');
  };
  
  return (
    <Box>
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center',
        mb: 3,
        py: 2
      }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <BedIcon fontSize="large" sx={{ mr: 1 }} /> 
          {predictedValue} 人
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          入院患者数予測
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, gap: 1 }}>
          <Chip 
            icon={<EventIcon />} 
            label={`${formatDate(target_date)}`} 
            variant="outlined" 
            color="primary"
          />
          <Chip 
            label={day_name} 
            variant="outlined"
            color={isHoliday ? "error" : "default"}
          />
          <Chip 
            icon={getSeasonIcon(season)} 
            label={getSeasonName(season)} 
            variant="outlined"
            color="secondary"
          />
        </Box>
      </Box>
      
      <Divider sx={{ mb: 2 }} />
      
      <Typography variant="subtitle2" gutterBottom>予測に使用した患者情報:</Typography>
      
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Paper variant="outlined" sx={{ p: 1, bgcolor: isHoliday ? '#fff8e1' : 'inherit' }}>
          <Typography variant="body2">
            <strong>予測日:</strong> {formatDate(target_date)} ({day_name})
            {isHoliday && ' (祝日)'}
          </Typography>
        </Paper>
        
        <Paper variant="outlined" sx={{ p: 1 }}>
          <Typography variant="body2">
            <strong>前日が祝日:</strong> {isPrevHoliday ? 'はい' : 'いいえ'}
          </Typography>
        </Paper>
        
        <Paper variant="outlined" sx={{ p: 1 }}>
          <Typography variant="body2">
            <strong>前日の総外来患者数:</strong> {features.total_outpatient} 人
          </Typography>
        </Paper>
        
        <Paper variant="outlined" sx={{ p: 1 }}>
          <Typography variant="body2">
            <strong>前日の紹介外来患者数:</strong> {features.intro_outpatient} 人
          </Typography>
        </Paper>
        
        <Paper variant="outlined" sx={{ p: 1 }}>
          <Typography variant="body2">
            <strong>前日の救急患者数:</strong> {features.ER} 人
          </Typography>
        </Paper>
        
        <Paper variant="outlined" sx={{ p: 1 }}>
          <Typography variant="body2">
            <strong>現在の病床数:</strong> {features.bed_count} 床
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
};

export default PredictionResult; 