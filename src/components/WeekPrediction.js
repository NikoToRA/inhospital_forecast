import React from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  useTheme,
  useMediaQuery,
  Chip
} from '@mui/material';
import { Line } from 'react-chartjs-2';
import BedIcon from '@mui/icons-material/Bed';
import EventIcon from '@mui/icons-material/Event';
import DateRangeIcon from '@mui/icons-material/DateRange';

const WeekPrediction = ({ weekPrediction, loading }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!weekPrediction || !weekPrediction.predictions || weekPrediction.predictions.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 300 }}>
        <Typography variant="body1" color="text.secondary">
          週間予測を実行すると、7日分の入院患者数予測が表示されます。
        </Typography>
      </Box>
    );
  }

  const { predictions, start_date } = weekPrediction;

  // 予測値の配列を取得（エラー処理を追加）
  const predictionValues = predictions.map(p => 
    typeof p.prediction === 'number' ? p.prediction : parseFloat(p.prediction) || 0
  );

  // チャートデータの作成
  const chartData = {
    labels: predictions.map(p => `${p.date.substring(5)} (${p.day_label ? p.day_label.charAt(0) : '?'})`),
    datasets: [
      {
        label: '入院患者数予測',
        data: predictionValues,
        borderColor: theme.palette.primary.main,
        backgroundColor: theme.palette.primary.light,
        tension: 0.3,
        fill: false,
      }
    ]
  };

  // チャートのオプション
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return `入院患者数: ${context.raw}人`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: false,
        ticks: {
          callback: function(value) {
            return value + '人';
          }
        }
      }
    }
  };

  // 最大値と最小値を計算
  const maxPrediction = Math.max(...predictionValues);
  const minPrediction = Math.min(...predictionValues);
  
  // 各予測値が最大か最小かをチェック
  const isMaxPrediction = (value) => value === maxPrediction;
  const isMinPrediction = (value) => value === minPrediction;

  // 日付のフォーマット変更
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    return dateStr.replace(/-/g, '/');
  };

  return (
    <Box sx={{ mt: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <DateRangeIcon sx={{ mr: 1, color: theme.palette.text.secondary }} />
        <Typography variant="h6">週間入院患者数予測</Typography>
      </Box>
      
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
        <Chip 
          icon={<EventIcon />} 
          label={`開始日: ${formatDate(start_date)}`} 
          variant="outlined" 
          color="primary"
        />
      </Box>
      
      {/* チャート表示 */}
      <Paper sx={{ p: 2, mb: 3, height: 300 }} elevation={2}>
        <Line data={chartData} options={chartOptions} />
      </Paper>
      
      {/* テーブル表示 */}
      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table size={isMobile ? "small" : "medium"}>
          <TableHead>
            <TableRow>
              <TableCell>日付</TableCell>
              <TableCell>曜日</TableCell>
              <TableCell align="right">外来患者数</TableCell>
              {!isMobile && <TableCell align="right">紹介外来</TableCell>}
              {!isMobile && <TableCell align="right">救急</TableCell>}
              <TableCell align="right">予測入院患者数</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {predictions.map((prediction, index) => {
              const isHoliday = prediction.features && prediction.features.public_holiday;
              const predValue = typeof prediction.prediction === 'number' 
                ? prediction.prediction 
                : parseFloat(prediction.prediction) || 0;
              
              return (
                <TableRow key={index} sx={isHoliday ? { bgcolor: '#fff8e1' } : {}}>
                  <TableCell>{prediction.date}</TableCell>
                  <TableCell>
                    {prediction.day_label}
                    {isHoliday && ' (祝)'}
                  </TableCell>
                  <TableCell align="right">
                    {prediction.features ? prediction.features.total_outpatient : '-'}
                  </TableCell>
                  {!isMobile && (
                    <TableCell align="right">
                      {prediction.features ? prediction.features.intro_outpatient : '-'}
                    </TableCell>
                  )}
                  {!isMobile && (
                    <TableCell align="right">
                      {prediction.features ? prediction.features.ER : '-'}
                    </TableCell>
                  )}
                  <TableCell align="right" sx={{ 
                    fontWeight: 'bold', 
                    color: isMaxPrediction(predValue) ? theme.palette.error.main : 
                           isMinPrediction(predValue) ? theme.palette.success.main : 
                           theme.palette.primary.main,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'flex-end'
                  }}>
                    <BedIcon fontSize="small" sx={{ mr: 0.5 }} />
                    {predValue}人
                    {isMaxPrediction(predValue) && 
                      <Chip size="small" label="最多" color="error" sx={{ ml: 1, height: 20 }} />}
                    {isMinPrediction(predValue) && 
                      <Chip size="small" label="最少" color="success" sx={{ ml: 1, height: 20 }} />}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
      
      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
        ※ 前日の外来患者数や曜日などの条件に基づいた予測です。土日祝日は自動的に外来患者数を調整しています。
      </Typography>
    </Box>
  );
};

export default WeekPrediction; 