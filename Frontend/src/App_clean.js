import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Chatbot from './components/Chatbot';
import Header from './components/Header';
import Footer from './components/Footer';

import HomePage from './pages/HomePage';
import LearnMorePage from './pages/LearnMorePage';
import ContactPage from './pages/ContactPage';
import ConnectPage from './pages/ConnectPage';
import SignupPage from './pages/SignupPage';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import RiskAssessmentPage from './pages/RiskAssessmentPage';
import EnhancedRiskAssessmentPage from './pages/EnhancedRiskAssessmentPage';
import NewRiskAssessmentPage from './pages/NewRiskAssessmentPage';
import ChartTest from './components/test/ChartTest';
import ReportPage from './pages/ReportPage';
import ProfilePage from './pages/ProfilePage';
import SDECataloguePage from './pages/SDECataloguePage';
import ModelInventoryPage from './pages/ModelInventory';
import DatabaseChatbot from './pages/DatabaseChatbot';
import './Css/App.css';

const PlaceholderPage = ({ title }) => (
  <div className="page-section">
    <h1>{title}</h1>
    <p>Content coming soon.</p>
  </div>
);

function ProtectedRoute({ user, children }) {
  // Allow access during signup flow
  const isSignupFlow = localStorage.getItem('signup_flow') === 'in_progress';
  
  if (!user || !user.email) {
    if (isSignupFlow) {
      // Allow access during signup flow
      return children;
    }
    return <Navigate to="/signup" replace />;
  }
  return children;
}

function App() {
  const [theme] = useState('light');
  const [user, setUser] = useState({
    name: localStorage.getItem('client_name') || null,
    email: localStorage.getItem('client_email') || null,
  });

  // Update user state when localStorage changes
  useEffect(() => {
    const handleStorageChange = () => {
      setUser({
        name: localStorage.getItem('client_name') || null,
        email: localStorage.getItem('client_email') || null,
      });
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  // Listen for logout events
  useEffect(() => {
    const handleLogout = () => {
      setUser({ name: null, email: null });
    };

    window.addEventListener('user-logout', handleLogout);
    return () => window.removeEventListener('user-logout', handleLogout);
  }, []);

  // Conditional rendering based on stored client data
  const showChatbot = localStorage.getItem('client_name') && localStorage.getItem('client_email');

  return (
    <div className={`App ${theme}-theme`}>
      <Router>
        <Header />
        <main className="main-content" style={{
          paddingTop: '64px',
          fontFamily: 'var(--font-family)',
          background: 'var(--background)',
          color: 'var(--foreground)'
        }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/connect" element={
              <ProtectedRoute user={user}>
                <ConnectPage />
              </ProtectedRoute>
            } />
            <Route path="/sde-catalogue" element={
              <ProtectedRoute user={user}>
                <SDECataloguePage />
              </ProtectedRoute>
            } />
            <Route path="/dashboard" element={
              <ProtectedRoute user={user}>
                <DashboardPage />
              </ProtectedRoute>
            } />
            <Route path="/risk-assessment" element={
              <ProtectedRoute user={user}>
                <NewRiskAssessmentPage />
              </ProtectedRoute>
            } />
            <Route path="/risk-assessment-old" element={
              <ProtectedRoute user={user}>
                <RiskAssessmentPage />
              </ProtectedRoute>
            } />
            <Route path="/risk-assessment-enhanced" element={
              <ProtectedRoute user={user}>
                <EnhancedRiskAssessmentPage />
              </ProtectedRoute>
            } />
            <Route path="/chart-test" element={<ChartTest />} />
            <Route path="/reports" element={
              <ProtectedRoute user={user}>
                <PlaceholderPage title="REPORTS Page" />
              </ProtectedRoute>
            } />
            <Route path="/report" element={
              <ProtectedRoute user={user}>
                <ReportPage />
              </ProtectedRoute>
            } />
            <Route path="/profile" element={
              <ProtectedRoute user={user}>
                <ProfilePage />
              </ProtectedRoute>
            } />
            <Route path="/models" element={
              <ProtectedRoute user={user}>
                <ModelInventoryPage />
              </ProtectedRoute>
            } />
            <Route path="/learn-more" element={<LearnMorePage />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/products" element={<PlaceholderPage title="PRODUCTS Page" />} />
            <Route path="/services" element={<PlaceholderPage title="SERVICES Page" />} />
            <Route path="/about" element={<PlaceholderPage title="ABOUT Page" />} />
            <Route path="/news" element={<PlaceholderPage title="NEWS Page" />} />
            <Route path="/database-chatbot" element={
              <ProtectedRoute user={user}>
                <DatabaseChatbot />
              </ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <Footer />
        {showChatbot && <Chatbot />}
      </Router>
    </div>
  );
}

export default App;
