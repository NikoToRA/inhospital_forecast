import React, { useEffect, useState } from 'react';
import { Box, Typography, Grid, Paper, CircularProgress, Skeleton } from '@mui/material';
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  BarElement,
  Title, 
  Tooltip, 
  Legend,
  ArcElement
} from 'chart.js';
import { Bar, Line, Pie } from 'react-chartjs-2';

// Chart.jsコンポーネントを登録
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const Dashboard = ({ prediction }) => {
  const [loading, setLoading] = useState(true);
  
  // ローディング表示のシミュレーション
  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1000);
    
    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Skeleton variant="rectangular" width="100%" height={300} />
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Skeleton variant="rectangular" width="100%" height={250} />
          </Grid>
          <Grid item xs={12} md={6}>
            <Skeleton variant="rectangular" width="100%" height={250} />
          </Grid>
        </Grid>
      </Box>
    );
  }

  // 曜日別平均入院患者数（サンプルデータ）
  const weekdayData = {
    labels: ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日'],
    datasets: [
      {
        label: '平均入院患者数',
        data: [28, 22, 21, 20, 22, 12, 10],
        backgroundColor: 'rgba(53, 162, 235, 0.5)',
      },
    ],
  };

  // 外来患者数と入院患者数の関係（サンプルデータ）
  const correlationData = {
    labels: ['100人以下', '100-300人', '300-500人', '500-700人', '700人以上'],
    datasets: [
      {
        label: '平均入院患者数',
        data: [8, 12, 18, 24, 30],
        backgroundColor: 'rgba(255, 99, 132, 0.5)',
      },
    ],
  };

  // 祝日と平日の比較（サンプルデータ）
  const holidayData = {
    labels: ['平日', '祝日'],
    datasets: [
      {
        label: '平均入院患者数',
        data: [22, 10],
        backgroundColor: [
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)',
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  // 過去の予測精度のトレンド（サンプルデータ）
  const trendData = {
    labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
    datasets: [
      {
        label: '実際の入院患者数',
        data: [18, 22, 20, 25, 27, 24],
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.5)',
      },
      {
        label: '予測入院患者数',
        data: [19, 20, 22, 24, 26, 23],
        borderColor: 'rgb(53, 162, 235)',
        backgroundColor: 'rgba(53, 162, 235, 0.5)',
      },
    ],
  };

  return (
    <Box>
      <Typography variant="subtitle1" gutterBottom>データ分析結果</Typography>
      
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" gutterBottom sx={{ fontSize: '1rem' }}>曜日別平均入院患者数</Typography>
        <Paper sx={{ p: 2, height: 300 }} elevation={0} variant="outlined">
          <Bar
            data={weekdayData}
            options={{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  position: 'top',
                },
                title: {
                  display: false,
                },
              },
            }}
          />
        </Paper>
      </Box>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Typography variant="h6" gutterBottom sx={{ fontSize: '1rem' }}>外来患者数と入院患者数の関係</Typography>
          <Paper sx={{ p: 2, height: 250 }} elevation={0} variant="outlined">
            <Bar
              data={correlationData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'top',
                  },
                  title: {
                    display: false,
                  },
                },
              }}
            />
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Typography variant="h6" gutterBottom sx={{ fontSize: '1rem' }}>祝日と平日の比較</Typography>
          <Paper sx={{ p: 2, height: 250 }} elevation={0} variant="outlined">
            <Pie
              data={holidayData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'top',
                  },
                  title: {
                    display: false,
                  },
                },
              }}
            />
          </Paper>
        </Grid>
        
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom sx={{ fontSize: '1rem' }}>過去の予測精度</Typography>
          <Paper sx={{ p: 2, height: 300 }} elevation={0} variant="outlined">
            <Line
              data={trendData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'top',
                  },
                  title: {
                    display: false,
                  },
                },
              }}
            />
          </Paper>
        </Grid>
      </Grid>
      
      <Box sx={{ mt: 3 }}>
        <Typography variant="body2" color="text.secondary">
          ※ このデータは説明用のサンプルデータです。実際のデータに基づいた分析結果ではありません。
        </Typography>
      </Box>
    </Box>
  );
};

export default Dashboard; 