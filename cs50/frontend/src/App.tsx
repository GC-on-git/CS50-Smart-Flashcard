import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect, lazy, Suspense } from 'react';
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const DeckDetail = lazy(() => import('./pages/DeckDetail'));
const StudySession = lazy(() => import('./pages/StudySession'));
const Settings = lazy(() => import('./pages/Settings'));
const Statistics = lazy(() => import('./pages/Statistics'));
import { apiClient } from './api/client';
import ToastContainer, { useToast } from './components/ToastContainer';
import { ToastProvider } from './contexts/ToastContext';
import { ThemeProvider } from './contexts/ThemeContext';
import './App.css';

function AppContent() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const { toasts, removeToast, success, error, info, warning } = useToast();

  useEffect(() => {
    const validateToken = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setIsAuthenticated(false);
        setLoading(false);
        return;
      }

      // Validate token by making an API call
      try {
        await apiClient.getProfile();
        setIsAuthenticated(true);
      } catch (error) {
        // Token is invalid, clear it
        localStorage.removeItem('access_token');
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    validateToken();
  }, []);

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <ThemeProvider>
      <ToastProvider value={{ success, error, info, warning }}>
        <Router>
          <ToastContainer toasts={toasts} removeToast={removeToast} />
          <Suspense fallback={<div className="loading">Loading...</div>}>
          <Routes>
            <Route 
              path="/login" 
              element={
                isAuthenticated ? <Navigate to="/" /> : <Login onLogin={() => setIsAuthenticated(true)} />
              } 
            />
            <Route 
              path="/register" 
              element={
                isAuthenticated ? <Navigate to="/" /> : <Register onRegister={() => setIsAuthenticated(true)} />
              } 
            />
            <Route 
              path="/" 
              element={
                isAuthenticated ? (
                  <Dashboard onLogout={() => setIsAuthenticated(false)} />
                ) : (
                  <Navigate to="/login" />
                )
              } 
            />
            <Route 
              path="/decks/:deckId" 
              element={
                isAuthenticated ? (
                  <DeckDetail onLogout={() => setIsAuthenticated(false)} />
                ) : (
                  <Navigate to="/login" />
                )
              } 
            />
            <Route 
              path="/decks/:deckId/study" 
              element={
                isAuthenticated ? (
                  <StudySession onLogout={() => setIsAuthenticated(false)} />
                ) : (
                  <Navigate to="/login" />
                )
              } 
            />
                <Route 
                  path="/settings" 
                  element={
                    isAuthenticated ? (
                      <Settings onLogout={() => setIsAuthenticated(false)} />
                    ) : (
                      <Navigate to="/login" />
                    )
                  } 
                />
                <Route 
                  path="/statistics" 
                  element={
                    isAuthenticated ? (
                      <Statistics onLogout={() => setIsAuthenticated(false)} />
                    ) : (
                      <Navigate to="/login" />
                    )
                  } 
                />
          </Routes>
          </Suspense>
        </Router>
      </ToastProvider>
    </ThemeProvider>
  );
}

function App() {
  return <AppContent />;
}

export default App;
