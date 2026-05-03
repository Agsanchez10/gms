import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import ReceptionDashboard from './pages/ReceptionDashboard';
import TrainerDashboard from './pages/TrainerDashboard';
import ManagerDashboard from './pages/ManagerDashboard';
import './App.css';

function App() {
  const { isAuthenticated, user } = useAuth();

  const getDashboard = () => {
    if (!isAuthenticated || !user) return <Navigate to="/login" replace />;
    switch (user.role) {
      case 'Reception': return <ReceptionDashboard />;
      case 'Trainer': return <TrainerDashboard />;
      case 'Manager': return <ManagerDashboard />;
      default: return <Navigate to="/login" replace />;
    }
  };

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/reception"
          element={isAuthenticated && (user?.role === 'Reception' || user?.role === 'Manager') ? <ReceptionDashboard /> : <Navigate to="/login" replace />}
        />
        <Route
          path="/trainer"
          element={isAuthenticated && (user?.role === 'Trainer' || user?.role === 'Manager') ? <TrainerDashboard /> : <Navigate to="/login" replace />}
        />
        <Route
          path="/manager"
          element={isAuthenticated && user?.role === 'Manager' ? <ManagerDashboard /> : <Navigate to="/login" replace />}
        />
        <Route path="/" element={getDashboard()} />
      </Routes>
    </Router>
  );
}

export default App;
