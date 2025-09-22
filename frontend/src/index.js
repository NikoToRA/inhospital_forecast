import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { Chart, registerables } from 'chart.js';
import ErrorBoundary from './components/ErrorBoundary';

// Chart.jsの登録
Chart.register(...registerables);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);

// global error handlers for quick surface
window.addEventListener('error', (event) => {
  // eslint-disable-next-line no-console
  console.error('Global error:', event.error || event.message);
});
window.addEventListener('unhandledrejection', (event) => {
  // eslint-disable-next-line no-console
  console.error('Unhandled promise rejection:', event.reason);
});

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals(); 