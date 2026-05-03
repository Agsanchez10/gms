import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { memberAPI, machineAPI, classAPI, planAPI } from '../services/api';

const STATUS_COLORS: Record<string, string> = {
  Available: '#28a745',
  'In Use': '#007bff',
  Maintenance: '#dc3545',
  Retired: '#6c757d',
  'Out of Order': '#6c757d',
};

// Normalize uppercase enum values from backend to display mixed-case
const normalizeStatus = (s: string) => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
const normalizeCategory = (s: string) => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
const normalizeMachine = (m: any) => ({
  ...m,
  status: normalizeStatus(m.status ?? ''),
  category: normalizeCategory(m.category ?? ''),
});
const normalizeMember = (m: any) => ({
  ...m,
  status: normalizeStatus(m.status ?? ''),
});

const MEMBER_STATUS_COLORS: Record<string, string> = {
  Active: '#28a745',
  Inactive: '#6c757d',
  Suspended: '#dc3545',
};

export default function ReceptionDashboard() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('dashboard');
  const [members, setMembers] = useState<any[]>([]);
  const [machines, setMachines] = useState<any[]>([]);
  const [classes, setClasses] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Plans list (for registration form)
  const [plans, setPlans] = useState<any[]>([]);

  // Register member form
  const [showRegisterForm, setShowRegisterForm] = useState(false);
  const [registerForm, setRegisterForm] = useState({
    first_name: '', last_name: '', email: '', phone_number: '', birth_date: '', plan_id: '',
  });
  const [registerError, setRegisterError] = useState('');
  const [registerSuccess, setRegisterSuccess] = useState('');
  const [registerLoading, setRegisterLoading] = useState(false);

  // Machine filter
  const [machineFilter, setMachineFilter] = useState('All');

  // Machine status editing
  const [statusUpdating, setStatusUpdating] = useState<number | null>(null);
  const [statusError, setStatusError] = useState('');

  // Add machine form
  const [showAddMachine, setShowAddMachine] = useState(false);
  const [addMachineForm, setAddMachineForm] = useState({
    machine_name: '', category: 'Cardio', purchase_date: '', status: 'Available', maintenance_notes: '',
  });
  const [addMachineError, setAddMachineError] = useState('');
  const [addMachineSuccess, setAddMachineSuccess] = useState('');
  const [addMachineLoading, setAddMachineLoading] = useState(false);

  // Class filters / sort
  const [classTypeFilter, setClassTypeFilter] = useState('All');
  const [classAvailFilter, setClassAvailFilter] = useState('All'); // All | Available | Full
  const [classSortBy, setClassSortBy] = useState<'start_time' | 'class_name' | 'enrolled'>('start_time');
  const [classSortDir, setClassSortDir] = useState<'asc' | 'desc'>('asc');

  // Class roster
  const [rosterClassId, setRosterClassId] = useState<number | null>(null);
  const [roster, setRoster] = useState<any[]>([]);
  const [rosterLoading, setRosterLoading] = useState(false);
  const [removeError, setRemoveError] = useState('');

  // Class enrollment
  const [enrollClassId, setEnrollClassId] = useState<number | null>(null);
  const [enrollMemberId, setEnrollMemberId] = useState<number | null>(null);
  const [enrollSearch, setEnrollSearch] = useState('');
  const [enrollResults, setEnrollResults] = useState<any[]>([]);
  const [enrollError, setEnrollError] = useState('');
  const [enrollSuccess, setEnrollSuccess] = useState('');
  const [enrollLoading, setEnrollLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [tab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (tab === 'members') {
        const [memberRes, planRes] = await Promise.all([
          memberAPI.list(0, 100),
          planAPI.list(),
        ]);
        setMembers(memberRes.data.map(normalizeMember));
        setPlans(planRes.data);
      } else if (tab === 'machines') {
        const res = await machineAPI.list(0, 100);
        setMachines(res.data.map(normalizeMachine));
      } else if (tab === 'classes') {
        const [classRes, memberRes] = await Promise.all([
          classAPI.list(0, 100),
          memberAPI.list(0, 100),
        ]);
        setClasses(classRes.data);
        setMembers(memberRes.data.map(normalizeMember));
      }
    } catch (error) {
      console.error('Error loading data:', error);
    }
    setLoading(false);
  };

  const handleLogout = () => {
    setUser(null);
    navigate('/login');
  };

  // ── Register member ──────────────────────────────────────────────
  const handleRegisterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setRegisterForm({ ...registerForm, [e.target.name]: e.target.value });
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegisterError('');
    setRegisterSuccess('');
    setRegisterLoading(true);
    try {
      console.log('Submitting form:', registerForm);
      await memberAPI.create(registerForm);
      setRegisterSuccess('Member registered successfully!');
      setRegisterForm({ first_name: '', last_name: '', email: '', phone_number: '', birth_date: '', plan_id: '' });
      setShowRegisterForm(false);
      
      // Reload members list
      setTimeout(async () => {
        try {
          const res = await memberAPI.list(0, 100);
          if (res.data && Array.isArray(res.data)) {
            setMembers(res.data.map(normalizeMember));
          }
        } catch (loadErr) {
          console.error('Error reloading members:', loadErr);
          setRegisterError('Member created but failed to reload list.');
        }
      }, 500);
    } catch (err: any) {
      console.error('Full error:', err);
      const errorMsg = err.response?.data?.detail || err.response?.data || err.message || 'Registration failed.';
      setRegisterError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
    } finally {
      setRegisterLoading(false);
    }
  };

  // ── Machine status ───────────────────────────────────────────────
  const handleStatusChange = async (machineId: number, newStatus: string) => {
    setStatusError('');
    setStatusUpdating(machineId);
    try {
      await machineAPI.updateStatus(machineId, newStatus.toUpperCase());
      setMachines((prev) =>
        prev.map((m) => m.machine_id === machineId ? { ...m, status: newStatus } : m)
      );
    } catch (err: any) {
      setStatusError(err.response?.data?.detail || 'Failed to update status.');
    } finally {
      setStatusUpdating(null);
    }
  };

  // ── Add machine ──────────────────────────────────────────────────
  const handleAddMachineSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddMachineError('');
    setAddMachineSuccess('');
    setAddMachineLoading(true);
    try {
      await machineAPI.create({ ...addMachineForm, status: addMachineForm.status.toUpperCase(), category: addMachineForm.category.toUpperCase() });
      setAddMachineSuccess('Machine added successfully!');
      setAddMachineForm({ machine_name: '', category: 'Cardio', purchase_date: '', status: 'Available', maintenance_notes: '' });
      setShowAddMachine(false);
    } catch (err: any) {
      setAddMachineError(err.response?.data?.detail || 'Failed to add machine.');
      setAddMachineLoading(false);
      return;
    }
    setAddMachineLoading(false);
    try {
      const res = await machineAPI.list(0, 100);
      setMachines(res.data.map(normalizeMachine));
    } catch {
      // list refresh failed silently; machine was still created
    }
  };

  // ── Roster ──────────────────────────────────────────────────────
  const openRoster = async (classId: number) => {
    setRosterClassId(classId);
    setEnrollClassId(null);
    setRemoveError('');
    setRosterLoading(true);
    try {
      const res = await classAPI.get(classId);
      setRoster(res.data.members ?? []);
    } catch {
      setRoster([]);
    } finally {
      setRosterLoading(false);
    }
  };

  const handleRemoveMember = async (classId: number, memberId: number) => {
    setRemoveError('');
    try {
      await classAPI.removeMember(classId, memberId);
      setRoster((prev) => prev.filter((m) => m.member_id !== memberId));
      // update member_count in classes list
      setClasses((prev) =>
        prev.map((c) =>
          c.class_id === classId ? { ...c, member_count: (c.member_count ?? 1) - 1 } : c
        )
      );
    } catch (err: any) {
      setRemoveError(err.response?.data?.detail || 'Failed to remove member.');
    }
  };

  // ── Enroll member in class ───────────────────────────────────────
  const openEnroll = (classId: number) => {
    setEnrollClassId(classId);
    setRosterClassId(null);
    setEnrollMemberId(null);
    setEnrollSearch('');
    setEnrollResults([]);
    setEnrollError('');
    setEnrollSuccess('');
  };

  const handleEnrollSearch = (query: string) => {
    setEnrollSearch(query);
    setEnrollMemberId(null);
    if (!query.trim()) { setEnrollResults([]); return; }
    const q = query.trim().toLowerCase();
    const results = members.filter((m) => {
      const idMatch = String(m.member_id) === q;
      const nameMatch = `${m.first_name} ${m.last_name}`.toLowerCase().includes(q);
      const emailMatch = m.email?.toLowerCase().includes(q);
      return idMatch || nameMatch || emailMatch;
    });
    setEnrollResults(results);
  };

  const handleEnrollSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!enrollClassId || !enrollMemberId) {
      setEnrollError('Please select a member from the search results.');
      return;
    }
    setEnrollError('');
    setEnrollSuccess('');
    setEnrollLoading(true);
    try {
      await classAPI.enrollMember(enrollClassId, enrollMemberId);
      setEnrollSuccess('Member enrolled successfully!');
      setEnrollClassId(null);
      const res = await classAPI.list(0, 100);
      setClasses(res.data);
    } catch (err: any) {
      setEnrollError(err.response?.data?.detail || 'Enrollment failed.');
    } finally {
      setEnrollLoading(false);
    }
  };

  const filteredMachines =
    machineFilter === 'All' ? machines : machines.filter((m) => m.status === machineFilter);

  return (
    <div className="app-container">
      <nav className="navbar">
        <h1>Reception Dashboard</h1>
        <div className="user-info">
          {user?.role === 'Manager' && (
            <button className="btn btn-secondary" onClick={() => navigate('/')} style={{ marginRight: '1rem' }}>
              ← Manager Dashboard
            </button>
          )}
          <span>{user?.first_name} {user?.last_name} ({user?.role})</span>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </nav>

      <div className="main-content">
        {/* Tab bar */}
        <div style={{ marginBottom: '2rem' }}>
          {['dashboard', 'members', 'machines', 'classes'].map((t) => (
            <button
              key={t}
              className={`btn ${tab === t ? '' : 'btn-secondary'}`}
              onClick={() => setTab(t)}
              style={{ marginLeft: t === 'dashboard' ? 0 : '0.5rem', textTransform: 'capitalize' }}
            >
              {t}
            </button>
          ))}
        </div>

        {/* ── Dashboard ─────────────────────────────────────────── */}
        {tab === 'dashboard' && (
          <div className="card">
            <h2>Welcome, {user?.first_name}!</h2>
            <p>Use the tabs above to:</p>
            <ul>
              <li><strong>Members</strong> – Register new members and view the member list</li>
              <li><strong>Machines</strong> – Check machine availability by status</li>
              <li><strong>Classes</strong> – Enroll members into available classes</li>
            </ul>
          </div>
        )}

        {/* ── Members ───────────────────────────────────────────── */}
        {tab === 'members' && (
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ marginBottom: 0 }}>Members</h2>
              <button
                className="btn"
                onClick={() => { setShowRegisterForm(!showRegisterForm); setRegisterError(''); setRegisterSuccess(''); }}
              >
                {showRegisterForm ? 'Cancel' : '+ Register New Member'}
              </button>
            </div>

            {registerSuccess && <div className="alert alert-success" style={{ marginTop: '1rem' }}>{registerSuccess}</div>}

            {showRegisterForm && (
              <form onSubmit={handleRegisterSubmit} style={{ marginTop: '1.5rem', borderTop: '1px solid #ddd', paddingTop: '1.5rem' }}>
                <h3 style={{ marginTop: 0 }}>New Member Registration</h3>
                {registerError && <div className="alert alert-error">{registerError}</div>}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label>First Name *</label>
                    <input name="first_name" value={registerForm.first_name} onChange={handleRegisterChange} required />
                  </div>
                  <div className="form-group">
                    <label>Last Name *</label>
                    <input name="last_name" value={registerForm.last_name} onChange={handleRegisterChange} required />
                  </div>
                  <div className="form-group">
                    <label>Phone Number *</label>
                    <input name="phone_number" value={registerForm.phone_number} onChange={handleRegisterChange} required placeholder="e.g. 5551234567" />
                  </div>
                  <div className="form-group">
                    <label>Email</label>
                    <input name="email" type="email" value={registerForm.email} onChange={handleRegisterChange} />
                  </div>
                  <div className="form-group">
                    <label>Date of Birth *</label>
                    <input name="birth_date" type="date" value={registerForm.birth_date} onChange={handleRegisterChange} required />
                  </div>
                  <div className="form-group">
                    <label>Membership Plan *</label>
                    <select name="plan_id" value={registerForm.plan_id} onChange={handleRegisterChange} required>
                      <option value="">-- Select a plan --</option>
                      {plans.map((p) => (
                        <option key={p.plan_id} value={p.plan_id}>
                          {p.type} — {p.duration} month{p.duration !== 1 ? 's' : ''} (${p.price})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <button type="submit" className="btn" disabled={registerLoading}>
                  {registerLoading ? 'Registering…' : 'Register Member'}
                </button>
              </form>
            )}

            {loading ? <p>Loading…</p> : (
              <table className="table" style={{ marginTop: '1.5rem' }}>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {members.map((m) => (
                    <tr key={m.member_id}>
                      <td>{m.member_id}</td>
                      <td>{m.first_name} {m.last_name}</td>
                      <td>{m.email || '—'}</td>
                      <td>{m.phone_number}</td>
                      <td>
                        <span style={{
                          backgroundColor: MEMBER_STATUS_COLORS[m.status] ?? '#6c757d',
                          color: '#fff', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.85rem',
                        }}>
                          {m.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ── Machines ────────────────────────────────────────────────── */}
        {tab === 'machines' && (
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0 }}>Machine Availability</h2>
              <button
                className="btn"
                onClick={() => { setShowAddMachine(!showAddMachine); setAddMachineError(''); setAddMachineSuccess(''); }}
              >
                {showAddMachine ? 'Cancel' : '+ Add Machine'}
              </button>
            </div>

            {addMachineSuccess && <div className="alert alert-success" style={{ marginBottom: '1rem' }}>{addMachineSuccess}</div>}

            {showAddMachine && (
              <form onSubmit={handleAddMachineSubmit} style={{ borderTop: '1px solid #ddd', paddingTop: '1.25rem', marginBottom: '1.5rem' }}>
                <h3 style={{ marginTop: 0 }}>New Machine</h3>
                {addMachineError && <div className="alert alert-error">{addMachineError}</div>}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label>Machine Name *</label>
                    <input
                      value={addMachineForm.machine_name}
                      onChange={(e) => setAddMachineForm({ ...addMachineForm, machine_name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Category *</label>
                    <select
                      value={addMachineForm.category}
                      onChange={(e) => setAddMachineForm({ ...addMachineForm, category: e.target.value })}
                      style={{ width: '100%', padding: '0.75rem', border: '1px solid #ddd', borderRadius: '4px' }}
                    >
                      <option value="Cardio">Cardio</option>
                      <option value="Strength">Strength</option>
                      <option value="Functional">Functional</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Purchase Date *</label>
                    <input
                      type="date"
                      value={addMachineForm.purchase_date}
                      onChange={(e) => setAddMachineForm({ ...addMachineForm, purchase_date: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Initial Status</label>
                    <select
                      value={addMachineForm.status}
                      onChange={(e) => setAddMachineForm({ ...addMachineForm, status: e.target.value })}
                      style={{ width: '100%', padding: '0.75rem', border: '1px solid #ddd', borderRadius: '4px' }}
                    >
                      <option value="Available">Available</option>
                      <option value="Maintenance">Maintenance</option>
                    </select>
                  </div>
                  <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                    <label>Maintenance Notes</label>
                    <input
                      value={addMachineForm.maintenance_notes}
                      onChange={(e) => setAddMachineForm({ ...addMachineForm, maintenance_notes: e.target.value })}
                      placeholder="Optional"
                    />
                  </div>
                </div>
                <button type="submit" className="btn" disabled={addMachineLoading}>
                  {addMachineLoading ? 'Adding…' : 'Add Machine'}
                </button>
              </form>
            )}

            {statusError && <div className="alert alert-error" style={{ marginBottom: '1rem' }}>{statusError}</div>}

            {/* Summary counts */}
            {!loading && (
              <div className="grid" style={{ marginBottom: '1.5rem' }}>
                {['All', 'Available', 'Maintenance', 'Retired'].map((s) => {
                  const count = s === 'All' ? machines.length : machines.filter((m) => m.status === s).length;
                  return (
                    <div
                      key={s}
                      className="stat-card"
                      style={{ cursor: 'pointer', border: machineFilter === s ? '2px solid #007bff' : '2px solid transparent' }}
                      onClick={() => setMachineFilter(s)}
                    >
                      <h3>{s}</h3>
                      <div className="number" style={{ color: s === 'Available' ? '#28a745' : s === 'Maintenance' ? '#dc3545' : s === 'Retired' ? '#6c757d' : '#333' }}>
                        {count}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {loading ? <p>Loading…</p> : (
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Category</th>
                    <th>Status</th>
                    <th>Change Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredMachines.map((m) => (
                    <tr key={m.machine_id}>
                      <td>{m.machine_id}</td>
                      <td>{m.machine_name}</td>
                      <td>{m.category}</td>
                      <td>
                        <span style={{
                          backgroundColor: STATUS_COLORS[m.status] ?? '#6c757d',
                          color: '#fff', padding: '0.25rem 0.6rem', borderRadius: '4px', fontSize: '0.85rem',
                        }}>
                          {m.status}
                        </span>
                      </td>
                      <td>
                        <select
                          value={m.status}
                          disabled={statusUpdating === m.machine_id}
                          onChange={(e) => handleStatusChange(m.machine_id, e.target.value)}
                          style={{ padding: '0.35rem 0.5rem', borderRadius: '4px', border: '1px solid #ddd', fontSize: '0.85rem', cursor: 'pointer' }}
                        >
                          <option value="Available">Available</option>
                          <option value="Maintenance">Maintenance</option>
                          <option value="Retired">Retired</option>
                        </select>
                        {statusUpdating === m.machine_id && <span style={{ marginLeft: '0.5rem', fontSize: '0.8rem', color: '#888' }}>Saving…</span>}
                      </td>
                    </tr>
                  ))}
                  {filteredMachines.length === 0 && (
                    <tr><td colSpan={5} style={{ textAlign: 'center', color: '#888' }}>No machines match this filter.</td></tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ── Classes ───────────────────────────────────────────── */}
        {tab === 'classes' && (
          <div className="card">
            <h2>Classes</h2>

            {enrollSuccess && <div className="alert alert-success">{enrollSuccess}</div>}
            {removeError && <div className="alert alert-error">{removeError}</div>}

            {/* Roster panel */}
            {rosterClassId !== null && (
              <div style={{ background: '#f8fff8', border: '1px solid #b8ddb8', borderRadius: '6px', padding: '1.25rem', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3 style={{ margin: 0 }}>
                    Roster — {classes.find((c) => c.class_id === rosterClassId)?.class_name}
                  </h3>
                  <button className="btn btn-secondary" style={{ padding: '0.3rem 0.8rem', fontSize: '0.85rem' }} onClick={() => setRosterClassId(null)}>Close</button>
                </div>
                {rosterLoading ? (
                  <p>Loading roster…</p>
                ) : roster.length === 0 ? (
                  <p style={{ color: '#888' }}>No members enrolled yet.</p>
                ) : (
                  <table className="table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Status</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {roster.map((m) => (
                        <tr key={m.member_id}>
                          <td>{m.member_id}</td>
                          <td>{m.first_name} {m.last_name}</td>
                          <td>{m.email || '—'}</td>
                          <td>
                            <span style={{ color: m.status === 'Active' ? '#28a745' : '#dc3545', fontWeight: 600 }}>{m.status}</span>
                          </td>
                          <td>
                            <button
                              className="btn btn-danger"
                              style={{ padding: '0.3rem 0.7rem', fontSize: '0.8rem' }}
                              onClick={() => handleRemoveMember(rosterClassId!, m.member_id)}
                            >
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {/* Enroll form */}
            {enrollClassId !== null && (
              <div style={{ background: '#f0f7ff', border: '1px solid #b8d9f8', borderRadius: '6px', padding: '1.25rem', marginBottom: '1.5rem' }}>
                <h3 style={{ marginTop: 0 }}>
                  Enroll Member — {classes.find((c) => c.class_id === enrollClassId)?.class_name}
                </h3>
                {enrollError && <div className="alert alert-error">{enrollError}</div>}
                <form onSubmit={handleEnrollSubmit}>
                  <div className="form-group">
                    <label>Search by ID, name, or email *</label>
                    <input
                      type="text"
                      value={enrollSearch}
                      onChange={(e) => handleEnrollSearch(e.target.value)}
                      placeholder="e.g. 42  |  John Smith  |  john@example.com"
                      autoFocus
                    />
                  </div>

                  {/* Search results list */}
                  {enrollSearch.trim() && enrollResults.length === 0 && (
                    <p style={{ color: '#888', margin: '0 0 1rem' }}>No members found.</p>
                  )}
                  {enrollResults.length > 0 && (
                    <div style={{ border: '1px solid #ddd', borderRadius: '4px', marginBottom: '1rem', maxHeight: '200px', overflowY: 'auto' }}>
                      {enrollResults.map((m) => (
                        <div
                          key={m.member_id}
                          onClick={() => { setEnrollMemberId(m.member_id); setEnrollSearch(`#${m.member_id} — ${m.first_name} ${m.last_name}`); setEnrollResults([]); }}
                          style={{
                            padding: '0.6rem 1rem',
                            cursor: 'pointer',
                            borderBottom: '1px solid #f0f0f0',
                            backgroundColor: enrollMemberId === m.member_id ? '#e8f4fd' : 'transparent',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                          }}
                        >
                          <span><strong>#{m.member_id}</strong> — {m.first_name} {m.last_name}{m.email ? ` · ${m.email}` : ''}</span>
                          <span style={{ fontSize: '0.8rem', color: m.status === 'Active' ? '#28a745' : '#dc3545' }}>{m.status}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {enrollMemberId && (
                    <div className="alert alert-info" style={{ marginBottom: '1rem' }}>
                      Selected: <strong>{enrollSearch}</strong>
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button type="submit" className="btn" disabled={enrollLoading || !enrollMemberId}>
                      {enrollLoading ? 'Enrolling…' : 'Confirm Enrollment'}
                    </button>
                    <button type="button" className="btn btn-secondary" onClick={() => setEnrollClassId(null)}>
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Filter / sort toolbar */}
            {!loading && (() => {
              const classTypes = ['All', ...Array.from(new Set(classes.map((c) => c.type).filter(Boolean)))];
              return (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <label style={{ fontWeight: 600, fontSize: '0.875rem' }}>Type:</label>
                    <select value={classTypeFilter} onChange={(e) => setClassTypeFilter(e.target.value)}
                      style={{ padding: '0.3rem 0.5rem', borderRadius: '4px', border: '1px solid #ddd', fontSize: '0.85rem' }}>
                      {classTypes.map((t) => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <label style={{ fontWeight: 600, fontSize: '0.875rem' }}>Availability:</label>
                    <select value={classAvailFilter} onChange={(e) => setClassAvailFilter(e.target.value)}
                      style={{ padding: '0.3rem 0.5rem', borderRadius: '4px', border: '1px solid #ddd', fontSize: '0.85rem' }}>
                      <option value="All">All</option>
                      <option value="Available">Has Spots</option>
                      <option value="Full">Full</option>
                    </select>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <label style={{ fontWeight: 600, fontSize: '0.875rem' }}>Sort:</label>
                    <select value={classSortBy} onChange={(e) => setClassSortBy(e.target.value as any)}
                      style={{ padding: '0.3rem 0.5rem', borderRadius: '4px', border: '1px solid #ddd', fontSize: '0.85rem' }}>
                      <option value="start_time">Start Time</option>
                      <option value="class_name">Class Name</option>
                      <option value="enrolled">Enrolled</option>
                    </select>
                    <button className="btn btn-secondary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}
                      onClick={() => setClassSortDir((d) => d === 'asc' ? 'desc' : 'asc')}>
                      {classSortDir === 'asc' ? '↑ Asc' : '↓ Desc'}
                    </button>
                  </div>
                </div>
              );
            })()}

            {loading ? <p>Loading…</p> : (() => {
              const now = new Date();
              const visible = classes
                .filter((cls) => new Date(cls.end_time ?? cls.start_time) >= now)
                .filter((cls) => classTypeFilter === 'All' || cls.type === classTypeFilter)
                .filter((cls) => {
                  if (classAvailFilter === 'All') return true;
                  const full = (cls.member_count ?? 0) >= cls.capacity;
                  return classAvailFilter === 'Full' ? full : !full;
                })
                .sort((a, b) => {
                  let cmp = 0;
                  if (classSortBy === 'start_time') cmp = new Date(a.start_time).getTime() - new Date(b.start_time).getTime();
                  else if (classSortBy === 'class_name') cmp = a.class_name.localeCompare(b.class_name);
                  else cmp = (a.member_count ?? 0) - (b.member_count ?? 0);
                  return classSortDir === 'asc' ? cmp : -cmp;
                });
              return (
                <table className="table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Class Name</th>
                      <th>Type</th>
                      <th>Enrolled / Cap</th>
                      <th>Start Time</th>
                      <th>End Time</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.length === 0 ? (
                      <tr><td colSpan={7} style={{ textAlign: 'center', color: '#888' }}>No current or upcoming classes match the selected filters.</td></tr>
                    ) : visible.map((cls) => {
                      const enrolled = cls.member_count ?? 0;
                      const full = enrolled >= cls.capacity;
                      const inProgress = new Date(cls.start_time) <= now && new Date(cls.end_time ?? cls.start_time) >= now;
                      return (
                        <tr key={cls.class_id}>
                          <td>{cls.class_id}</td>
                          <td>
                            {cls.class_name}
                            {inProgress && <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', background: '#007bff', color: '#fff', borderRadius: '4px', padding: '0.1rem 0.4rem' }}>In Progress</span>}
                          </td>
                          <td>{cls.type}</td>
                          <td>
                            <span style={{ color: full ? '#dc3545' : '#28a745', fontWeight: 600 }}>
                              {enrolled} / {cls.capacity}
                            </span>
                            {full && <span style={{ marginLeft: '0.5rem', fontSize: '0.8rem', color: '#dc3545' }}>FULL</span>}
                          </td>
                          <td>{new Date(cls.start_time).toLocaleString()}</td>
                          <td>{cls.end_time ? new Date(cls.end_time).toLocaleString() : '—'}</td>
                          <td style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                            <button
                              className="btn"
                              style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                              disabled={full}
                              onClick={() => openEnroll(cls.class_id)}
                            >
                              Enroll
                            </button>
                            <button
                              className="btn btn-secondary"
                              style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                              onClick={() => openRoster(cls.class_id)}
                            >
                              View Roster
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
}
