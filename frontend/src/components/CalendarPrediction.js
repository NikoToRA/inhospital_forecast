import React, { useEffect, useMemo, useState } from 'react';
import { Box, Grid, Paper, Typography, useTheme, Chip, CircularProgress } from '@mui/material';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import { makeMonthPrediction } from '../services/api';

const getYearMonth = (date) => ({ year: date.getFullYear(), month: date.getMonth() + 1 });
const pad2 = (n) => String(n).padStart(2, '0');

const buildCalendarMatrix = (year, month) => {
  const first = new Date(year, month - 1, 1);
  const last = new Date(year, month, 0);
  const firstWeekday = first.getDay(); // 0=Sun..6=Sat
  const daysInMonth = last.getDate();
  const weeks = [];
  let week = new Array(7).fill(null);
  let day = 1;

  // Fill leading blanks
  for (let i = 0; i < firstWeekday; i++) week[i] = null;

  for (let i = firstWeekday; i < 7; i++) {
    week[i] = day++;
  }
  weeks.push(week);

  while (day <= daysInMonth) {
    week = new Array(7).fill(null);
    for (let i = 0; i < 7 && day <= daysInMonth; i++) {
      week[i] = day++;
    }
    weeks.push(week);
  }
  return weeks;
};

const MonthCalendar = ({ title, year, month, predictionsMap, minValue, maxValue }) => {
  const theme = useTheme();
  const matrix = useMemo(() => buildCalendarMatrix(year, month), [year, month]);

  const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), hi);
  const valueToColor = (v) => {
    if (v == null || isNaN(v) || !isFinite(v)) return undefined;
    const min = minValue ?? v;
    const max = maxValue ?? v;
    const range = Math.max(0.0001, max - min);
    const t = clamp((v - min) / range, 0, 1); // 0..1
    // Map t: 0 (low) -> green-ish, 1 (high) -> red-ish via HSL
    const hue = 120 * (1 - t); // 120: green, 0: red
    const lightness = 90 - 40 * t; // lighter for low, darker for high
    return `hsl(${hue}, 80%, ${lightness}%)`;
  };

  const renderCell = (d, i) => {
    if (!d) return (
      <Box key={`empty-${i}`} sx={{ p: 1, minHeight: 64 }} />
    );
    const dateStr = `${year}-${pad2(month)}-${pad2(d)}`;
    const pred = predictionsMap[dateStr];
    const valueNum = pred ? Number(pred.prediction) : null;
    const value = valueNum != null ? valueNum.toFixed(1) : '';
    const isHoliday = pred?.is_holiday;
    const isWeekend = pred?.is_weekend;
    const bg = valueNum != null ? valueToColor(valueNum) : undefined;

    return (
      <Paper
        key={dateStr}
        variant="outlined"
        sx={{
          p: 1,
          minHeight: 80,
          borderColor: isHoliday ? theme.palette.error.main : undefined,
          bgcolor: bg || (isHoliday ? '#fff8e1' : undefined),
          transition: 'background-color 0.2s ease',
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="subtitle2" color={isWeekend ? 'text.secondary' : 'text.primary'}>
            {d}
          </Typography>
          {isHoliday && <Chip size="small" label="祝" color="error" variant="outlined" />}
        </Box>
        {value && (
          <Typography variant="caption" sx={{ mt: 0.5, fontWeight: 500, opacity: 0.85, color: theme.palette.text.primary }}>
            {value}人
          </Typography>
        )}
      </Paper>
    );
  };

  return (
    <Box sx={{ mb: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <CalendarMonthIcon sx={{ mr: 1 }} />
        <Typography variant="h6">{title}</Typography>
      </Box>
      <Grid container spacing={1}>
        {['日','月','火','水','木','金','土'].map((w) => (
          <Grid item xs={12/7} key={w} sx={{ flexBasis: '14.28%', maxWidth: '14.28%' }}>
            <Typography variant="caption" color="text.secondary">{w}</Typography>
          </Grid>
        ))}
      </Grid>
      {matrix.map((week, wi) => (
        <Grid container spacing={1} key={`w-${wi}`} sx={{ mt: 0.5 }}>
          {week.map((d, di) => (
            <Grid item xs={12/7} key={`c-${wi}-${di}`} sx={{ flexBasis: '14.28%', maxWidth: '14.28%' }}>
              {renderCell(d, di)}
            </Grid>
          ))}
        </Grid>
      ))}
    </Box>
  );
};

const CalendarPrediction = ({ inputs, monthCur, monthNext, loading }) => {
  const today = new Date();
  const { year, month } = getYearMonth(today);
  const next = new Date(today.getFullYear(), today.getMonth() + 1, 1);
  const nextYM = getYearMonth(next);

  const [curMap, setCurMap] = useState({});
  const [nextMap, setNextMap] = useState({});
  const [minMax, setMinMax] = useState({ min: null, max: null });

  useEffect(() => {
    const toMap = (arr) => Object.fromEntries(arr.map(p => [p.date, p]));
    setCurMap(toMap(monthCur?.predictions || []));
    setNextMap(toMap(monthNext?.predictions || []));
    const vals = [];
    (monthCur?.predictions || []).forEach(p => { if (p?.prediction != null) vals.push(Number(p.prediction)); });
    (monthNext?.predictions || []).forEach(p => { if (p?.prediction != null) vals.push(Number(p.prediction)); });
    if (vals.length) {
      setMinMax({ min: Math.min(...vals), max: Math.max(...vals) });
    }
  }, [monthCur, monthNext]);

  return (
    <Box>
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
          <CircularProgress size={24} />
        </Box>
      )}
      {/* 凡例（ヒートマップの色スケール） */}
      {(minMax.min != null && minMax.max != null) && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <Typography variant="caption">少ない</Typography>
          <Box sx={{
            height: 10,
            flexGrow: 1,
            background: 'linear-gradient(90deg, hsl(120,80%,90%) 0%, hsl(60,80%,70%) 50%, hsl(0,80%,50%) 100%)',
            borderRadius: 5,
          }} />
          <Typography variant="caption">多い</Typography>
          <Typography variant="caption" sx={{ ml: 1, color: 'text.secondary' }}>{minMax.min.toFixed(1)}〜{minMax.max.toFixed(1)}人</Typography>
        </Box>
      )}

      <MonthCalendar title={`${year}年${month}月`} year={year} month={month} predictionsMap={curMap} minValue={minMax.min} maxValue={minMax.max} />
      <MonthCalendar title={`${nextYM.year}年${nextYM.month}月`} year={nextYM.year} month={nextYM.month} predictionsMap={nextMap} minValue={minMax.min} maxValue={minMax.max} />
    </Box>
  );
};

export default CalendarPrediction;
