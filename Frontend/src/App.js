import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Chatbot from './components/Chatbot';
import Header from './components/Header';
import Footer from './components/Footer';
import ScrollToTop from './components/ScrollToTop';
import PageTransition from './components/PageTransition';

import HomePage from './pages/HomePage';
import LearnMorePage from './pages/LearnMorePage';
import ContactPage from './pages/ContactPage';
import ConnectPage from './pages/ConnectPage';
import SignupPage from './pages/SignupPage';
import LoginPage from './pages/LoginPage';
import RoleSignupPage from './pages/RoleSignupPage';
import RoleLoginPage from './pages/RoleLoginPage';
import DashboardPage from './pages/DashboardPage';
import DiscoverPage from './pages/DiscoverPage';
import RiskAssessmentPage from './pages/RiskAssessmentPage';
import EnhancedRiskAssessmentPage from './pages/EnhancedRiskAssessmentPage';
import NewRiskAssessmentPage from './pages/NewRiskAssessmentPage';

import ReportPage from './pages/ReportPage';
import ProfilePage from './pages/ProfilePage';
import SDECataloguePage from './pages/SDECataloguePage';
import ModelInventoryPage from './pages/ModelInventory';
import DatabaseChatbot from './pages/DatabaseChatbot';
import About from './pages/About'; // Import the About page
import Compliance from './pages/Compliance'; // Import the new Compliance component
import HowToUsePage from './pages/HowToUsePage'; // Import the How to Use page
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
  const [theme] = useState('light'); // Remove setTheme if not used, or remove the whole line if theme is not used
  const [user, setUser] = useState({
    name: localStorage.getItem('client_name') || null,
    email: localStorage.getItem('client_email') || null,
  });

  // Sync user state with localStorage on storage events (cross-tab)
  useEffect(() => {
    const syncUser = () => {
      setUser({
        name: localStorage.getItem('client_name') || null,
        email: localStorage.getItem('client_email') || null,
      });
    };
    window.addEventListener('storage', syncUser);
    return () => window.removeEventListener('storage', syncUser);
  }, []);

  // Sync user state with localStorage on location change (same tab)
  useEffect(() => {
    const checkLocalStorage = () => {
      const newName = localStorage.getItem('client_name') || null;
      const newEmail = localStorage.getItem('client_email') || null;
      if (newName !== user.name || newEmail !== user.email) {
        setUser({
          name: newName,
          email: newEmail,
        });
      }
    };

    // Check immediately and on route changes
    checkLocalStorage();
    window.addEventListener('popstate', checkLocalStorage);
    return () => window.removeEventListener('popstate', checkLocalStorage);
  }, [user.name, user.email]);

  useEffect(() => {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  return (
    <Router>
      <ScrollToTop />
      <Header />
      <main className="main-content" style={{
        paddingTop: '64px', // header height only
        fontFamily: 'var(--font-family)',
        background: 'var(--background)',
        color: 'var(--foreground)'
      }}>
        <PageTransition>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/connect" element={
              <ProtectedRoute user={user}>
                <ConnectPage />
              </ProtectedRoute>
            } />
            <Route path="/discover" element={
              <ProtectedRoute user={user}>
                <DiscoverPage />
              </ProtectedRoute>
            } />
            {/* NEW SDE CATALOGUE ROUTE */}
            <Route path="/sde-catalogue" element={
              <ProtectedRoute user={user}>
                <SDECataloguePage />
              </ProtectedRoute>
            } />
            {/* END NEW SDE CATALOGUE ROUTE */}
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
            <Route path="/reports" element={
              <ProtectedRoute user={user}>
                <PlaceholderPage title="REPORTS Page" />
              </ProtectedRoute>
            } />
            <Route path="/report" element={
              <ProtectedRoute user={user}>
                <ReportPage theme={theme} />
              </ProtectedRoute>
            } />
            <Route path="/compliance" element={
              <ProtectedRoute user={user}>
                <Compliance />
              </ProtectedRoute>
            } />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/signup" element={<SignupPage setUser={setUser} />} />
            <Route path="/login" element={<LoginPage setUser={setUser} />} />
            <Route path="/role-signup" element={<RoleSignupPage />} />
            <Route path="/role-login" element={<RoleLoginPage setUser={setUser} />} />
            <Route path="/analysis" element={<PlaceholderPage title="ANALYTICS Page" />} />
            <Route path="/solutions" element={<PlaceholderPage title="SOLUTIONS Page" />} />
            <Route path="/resources" element={<PlaceholderPage title="RESOURCES Page" />} />
            <Route path="/profile" element={
              <ProtectedRoute user={user}>
                <ProfilePage />
              </ProtectedRoute>
            } />
            <Route path="/about" element={<About />} />
            <Route path="/how-to-use" element={<HowToUsePage />} />
            <Route path="/get-started" element={<PlaceholderPage title="Get Started Page" />} />
            <Route path="/learn-more" element={<LearnMorePage />} />
            <Route path="/about/vision" element={<LearnMorePage />} />
            <Route path="/products/data-discovery" element={<PlaceholderPage title="Data Discovery & Classification" />} />
            <Route path="/products/risk-scoring" element={<PlaceholderPage title="PII Risk Scoring Engine" />} />
            <Route path="/products/data-protection" element={<PlaceholderPage title="Smart Data Protection" />} />
            <Route path="/products/compliance-automation" element={<PlaceholderPage title="Compliance Automation" />} />
            <Route path="/products/alerts-audit" element={<PlaceholderPage title="Real-Time Alerts & Audit Logs" />} />
            <Route path="/analysis/risk-dashboard" element={<PlaceholderPage title="Risk Dashboard" />} />
            <Route path="/analysis/compliance-insights" element={<PlaceholderPage title="Compliance Insights" />} />
            <Route path="/analysis/trends-history" element={<PlaceholderPage title="Trends & History" />} />
            <Route path="/solutions/financial" element={<PlaceholderPage title="For Financial Services" />} />
            <Route path="/solutions/healthcare" element={<PlaceholderPage title="For Healthcare & Life Sciences" />} />
            <Route path="/solutions/retail" element={<PlaceholderPage title="For Retail & E-Commerce" />} />
            <Route path="/solutions/cloud-native" element={<PlaceholderPage title="For Cloud-Native Enterprises" />} />
            <Route path="/resources/case-studies" element={<PlaceholderPage title="Case Studies" />} />
            <Route path="/resources/blogs" element={<PlaceholderPage title="Blogs & Security Insights" />} />
            <Route path="/resources/whitepapers" element={<PlaceholderPage title="Whitepapers / Reports" />} />
            <Route path="/resources/demos" element={<PlaceholderPage title="Product Demos" />} />
            <Route path="/about/careers" element={<PlaceholderPage title="Careers" />} />
            <Route path="/model-inventory" element={<ModelInventoryPage />} />
            <Route path="/ask" element={
              <ProtectedRoute user={user}>
                <DatabaseChatbot />
              </ProtectedRoute>
            } />
            {/* Redirect all unknown routes to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </PageTransition>
      </main>
      <Footer />
      {/* Chatbot - Available on all pages */}
      <Chatbot />
    </Router>
  );
}

export default App;
