import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { staffAPI } from '../services/api';
import './LoginPage.css';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [redirectRole, setRedirectRole] = useState<string | null>(null);
  const navigate = useNavigate();
  const { setUser } = useAuth();

  // Handle navigation after user is set
  useEffect(() => {
    if (redirectRole) {
      if (redirectRole === 'Reception') {
        navigate('/reception');
      } else if (redirectRole === 'Trainer') {
        navigate('/trainer');
      } else if (redirectRole === 'Manager') {
        navigate('/manager');
      } else {
        navigate('/');
      }
      setRedirectRole(null);
    }
  }, [redirectRole, navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await staffAPI.login(email, password);
      setUser(response.data);
      
      // Set role for navigation after state updates
      setRedirectRole(response.data.role);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>Gym Management System</h1>
        <h2>Staff Login</h2>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <button type="submit" className="btn btn-login" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="login-info">
          <p><strong>Demo Credentials:</strong></p>
          <p>Role: Manager | Email: manager@gym.com | Password: password123</p>
          <p>Role: Trainer | Email: trainer@gym.com | Password: password123</p>
          <p>Role: Reception | Email: reception@gym.com | Password: password123</p>
        </div>
      </div>
    </div>
  );
}
