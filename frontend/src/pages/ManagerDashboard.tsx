import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { managerAPI, memberAPI } from '../services/api';

const MEMBER_STATUS_COLORS: Record<string, string> = {
  Active: '#28a745',
  Inactive: '#6c757d',
  Suspended: '#dc3545',
};

const normalizeMemberStatus = (s: string) =>
  s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : s;

export default function ManagerDashboard() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('overview');
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [machineAnalytics, setMachineAnalytics] = useState<any[]>([]);
  const [machineDays, setMachineDays] = useState(30);
  const [machineTypeFilter, setMachineTypeFilter] = useState('All');
  const [machineSortBy, setMachineSortBy] = useState<'total_usages' | 'total_hours' | 'unique_members'>('total_usages');
  const [machineSortDir, setMachineSortDir] = useState<'desc' | 'asc'>('desc');
  const [classAnalytics, setClassAnalytics] = useState<any[]>([]);
  const [classTypeFilter, setClassTypeFilter] = useState('All');
  const [classSortBy, setClassSortBy] = useState<'enrolled_count' | 'capacity' | 'occupancy_percentage'>('enrolled_count');
  const [classSortDir, setClassSortDir] = useState<'desc' | 'asc'>('desc');
  const [membershipStats, setMembershipStats] = useState<any>(null);
  const [members, setMembers] = useState<any[]>([]);
  const [memberSearch, setMemberSearch] = useState('');
  const [memberStatusFilter, setMemberStatusFilter] = useState('All');
  const [changingStatusFor, setChangingStatusFor] = useState<number | null>(null);
  const [pendingStatus, setPendingStatus] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [tab]);

  useEffect(() => {
    if (tab === 'machines') loadMachineData();
  }, [machineDays]);

  const loadMachineData = async () => {
    setLoading(true);
    try {
      const res = await managerAPI.getMachineUsageAnalytics(machineDays);
      setMachineAnalytics(res.data);
    } catch (error) {
      console.error('Error loading machine data:', error);
    }
    setLoading(false);
  };

  const loadData = async () => {
    setLoading(true);
    try {
      if (tab === 'overview') {
        const res = await managerAPI.getDashboardOverview();
        setDashboardData(res.data);
      } else if (tab === 'machines') {
        const res = await managerAPI.getMachineUsageAnalytics(machineDays);
        setMachineAnalytics(res.data);
      } else if (tab === 'classes') {
        const res = await managerAPI.getClassEnrollmentAnalytics();
        setClassAnalytics(res.data);
      } else if (tab === 'members') {
        const [statsRes, membersRes] = await Promise.all([
          managerAPI.getMembershipStatusAnalytics(),
          memberAPI.list(0, 1000),
        ]);
        setMembershipStats(statsRes.data);
        setMembers(membersRes.data.map((m: any) => ({ ...m, status: normalizeMemberStatus(m.status) })));
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

  const handleStatusUpdate = async (memberId: number) => {
    try {
      await memberAPI.updateStatus(memberId, pendingStatus);
      // Re-fetch to get accurate derived status
      const membersRes = await memberAPI.list(0, 1000);
      setMembers(membersRes.data.map((m: any) => ({ ...m, status: normalizeMemberStatus(m.status) })));
      setChangingStatusFor(null);
    } catch (err) {
      console.error('Failed to update member status:', err);
    }
  };

  return (
    <div className="app-container">
      <nav className="navbar">
        <h1>Manager Dashboard</h1>
        <div className="user-info">
          <button className="btn btn-secondary" onClick={() => navigate('/reception')} style={{ marginRight: '0.5rem' }}>
            View Reception
          </button>          
          <span>{user?.first_name} {user?.last_name} ({user?.role})</span>
          <button className="logout-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      <div className="main-content">
        <div style={{ marginBottom: '2rem' }}>
          <button
            className={`btn ${tab === 'overview' ? '' : 'btn-secondary'}`}
            onClick={() => setTab('overview')}
          >
            Overview
          </button>
          <button
            className={`btn ${tab === 'machines' ? '' : 'btn-secondary'}`}
            onClick={() => setTab('machines')}
            style={{ marginLeft: '0.5rem' }}
          >
            Machine Usage
          </button>
          <button
            className={`btn ${tab === 'classes' ? '' : 'btn-secondary'}`}
            onClick={() => setTab('classes')}
            style={{ marginLeft: '0.5rem' }}
          >
            Classes
          </button>
          <button
            className={`btn ${tab === 'members' ? '' : 'btn-secondary'}`}
            onClick={() => setTab('members')}
            style={{ marginLeft: '0.5rem' }}
          >
            Members
          </button>
        </div>

        {tab === 'overview' && (
          <div>
            {loading ? (
              <p>Loading...</p>
            ) : dashboardData ? (
              <div className="grid">
                <div className="stat-card">
                  <h3>Total Members</h3>
                  <div className="number">{dashboardData.total_members}</div>
                </div>
                <div className="stat-card">
                  <h3>Active Members</h3>
                  <div className="number">{dashboardData.active_members}</div>
                </div>
                <div className="stat-card">
                  <h3>Staff</h3>
                  <div className="number">{dashboardData.total_staff}</div>
                </div>
                <div className="stat-card">
                  <h3>Machines</h3>
                  <div className="number">{dashboardData.total_machines}</div>
                </div>
                <div className="stat-card">
                  <h3>Available Machines</h3>
                  <div className="number">{dashboardData.available_machines}</div>
                </div>
                <div className="stat-card">
                  <h3>Classes</h3>
                  <div className="number">{dashboardData.total_classes}</div>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {tab === 'machines' && (() => {
          const periodLabel: Record<number, string> = { 30: '30 Days', 60: '60 Days', 90: '90 Days', 180: '6 Months', 365: '1 Year' };
          const machineTypes = ['All', ...Array.from(new Set(machineAnalytics.map((s) => s.category).filter(Boolean)))];
          const sortIcon = (col: string) => machineSortBy === col ? (machineSortDir === 'desc' ? ' ▼' : ' ▲') : ' ↕';
          const toggleSort = (col: typeof machineSortBy) => {
            if (machineSortBy === col) setMachineSortDir((d) => (d === 'desc' ? 'asc' : 'desc'));
            else { setMachineSortBy(col); setMachineSortDir('desc'); }
          };
          const filtered = machineAnalytics
            .filter((s) => machineTypeFilter === 'All' || s.category === machineTypeFilter)
            .sort((a, b) => (machineSortDir === 'desc' ? b[machineSortBy] - a[machineSortBy] : a[machineSortBy] - b[machineSortBy]));
          return (
            <div className="card">
              <h2>Machine Usage Analytics</h2>

              {/* Time period selector */}
              <div style={{ marginBottom: '1rem' }}>
                <strong style={{ marginRight: '0.5rem' }}>Period:</strong>
                {[30, 60, 90, 180, 365].map((d) => (
                  <button
                    key={d}
                    className={`btn ${machineDays === d ? '' : 'btn-secondary'}`}
                    onClick={() => setMachineDays(d)}
                    style={{ marginRight: '0.4rem' }}
                  >
                    {periodLabel[d]}
                  </button>
                ))}
              </div>

              {/* Type filter */}
              <div style={{ marginBottom: '1rem' }}>
                <strong style={{ marginRight: '0.5rem' }}>Type:</strong>
                <select
                  value={machineTypeFilter}
                  onChange={(e) => setMachineTypeFilter(e.target.value)}
                  style={{ padding: '0.35rem 0.6rem', borderRadius: '4px', border: '1px solid #ccc' }}
                >
                  {machineTypes.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              {loading ? (
                <p>Loading...</p>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Machine</th>
                      <th>Type</th>
                      <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('total_usages')}>Usage Count{sortIcon('total_usages')}</th>
                      <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('total_hours')}>Total Hours{sortIcon('total_hours')}</th>
                      <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('unique_members')}>Unique Members{sortIcon('unique_members')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((stat) => (
                      <tr key={stat.machine_id}>
                        <td>{stat.machine_name}</td>
                        <td>{stat.category ?? '—'}</td>
                        <td>{stat.total_usages}</td>
                        <td>{stat.total_hours}</td>
                        <td>{stat.unique_members}</td>
                      </tr>
                    ))}
                    {filtered.length === 0 && (
                      <tr><td colSpan={5} style={{ textAlign: 'center' }}>No data found</td></tr>
                    )}
                  </tbody>
                </table>
              )}
            </div>
          );
        })()}

        {tab === 'classes' && (() => {
          const classTypes = ['All', ...Array.from(new Set(classAnalytics.map((s) => s.type).filter(Boolean)))];
          const sortIcon = (col: string) => classSortBy === col ? (classSortDir === 'desc' ? ' ▼' : ' ▲') : ' ↕';
          const toggleSort = (col: typeof classSortBy) => {
            if (classSortBy === col) setClassSortDir((d) => (d === 'desc' ? 'asc' : 'desc'));
            else { setClassSortBy(col); setClassSortDir('desc'); }
          };
          const filtered = classAnalytics
            .filter((s) => classTypeFilter === 'All' || s.type === classTypeFilter)
            .sort((a, b) => (classSortDir === 'desc' ? b[classSortBy] - a[classSortBy] : a[classSortBy] - b[classSortBy]));
          return (
            <div className="card">
              <h2>Class Enrollment Analytics</h2>

              {/* Type filter */}
              <div style={{ marginBottom: '1rem' }}>
                <strong style={{ marginRight: '0.5rem' }}>Type:</strong>
                <select
                  value={classTypeFilter}
                  onChange={(e) => setClassTypeFilter(e.target.value)}
                  style={{ padding: '0.35rem 0.6rem', borderRadius: '4px', border: '1px solid #ccc' }}
                >
                  {classTypes.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              {loading ? (
                <p>Loading...</p>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Class Name</th>
                      <th>Type</th>
                      <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('enrolled_count')}>Enrolled{sortIcon('enrolled_count')}</th>
                      <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('capacity')}>Capacity{sortIcon('capacity')}</th>
                      <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('occupancy_percentage')}>Occupancy %{sortIcon('occupancy_percentage')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((stat) => (
                      <tr key={stat.class_id}>
                        <td>{stat.class_name}</td>
                        <td>{stat.type}</td>
                        <td>{stat.enrolled_count}</td>
                        <td>{stat.capacity}</td>
                        <td>{stat.occupancy_percentage}%</td>
                      </tr>
                    ))}
                    {filtered.length === 0 && (
                      <tr><td colSpan={5} style={{ textAlign: 'center' }}>No data found</td></tr>
                    )}
                  </tbody>
                </table>
              )}
            </div>
          );
        })()}

        {tab === 'members' && (
          <div className="card">
            <h2>Members</h2>
            {loading ? (
              <p>Loading...</p>
            ) : (
              <>
                {/* Summary stats */}
                {membershipStats && (
                  <div className="grid" style={{ marginBottom: '1.5rem' }}>
                    {[['Total Members', membershipStats.total_members, '#333'], ['Active', membershipStats.active, '#28a745'], ['Inactive', membershipStats.inactive, '#6c757d'], ['Suspended', membershipStats.suspended, '#dc3545']].map(([label, val, color]) => (
                      <div key={label as string} className="stat-card">
                        <h3>{label}</h3>
                        <div className="number" style={{ color: color as string }}>{val}</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Search + filter toolbar */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center', marginBottom: '1rem' }}>
                  <input
                    type="text"
                    placeholder="Search by name or email…"
                    value={memberSearch}
                    onChange={(e) => setMemberSearch(e.target.value)}
                    style={{ padding: '0.4rem 0.75rem', borderRadius: '4px', border: '1px solid #ccc', fontSize: '0.875rem', minWidth: '220px' }}
                  />
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <label style={{ fontWeight: 600, fontSize: '0.875rem' }}>Status:</label>
                    <select value={memberStatusFilter} onChange={(e) => setMemberStatusFilter(e.target.value)}
                      style={{ padding: '0.35rem 0.6rem', borderRadius: '4px', border: '1px solid #ccc', fontSize: '0.875rem' }}>
                      <option value="All">All</option>
                      <option value="Active">Active</option>
                      <option value="Inactive">Inactive</option>
                      <option value="Suspended">Suspended</option>
                    </select>
                  </div>
                </div>

                {/* Member table */}
                {(() => {
                  const q = memberSearch.trim().toLowerCase();
                  const visible = members
                    .filter((m) => memberStatusFilter === 'All' || m.status === memberStatusFilter)
                    .filter((m) => !q || `${m.first_name} ${m.last_name}`.toLowerCase().includes(q) || (m.email ?? '').toLowerCase().includes(q));
                  return (
                    <table className="table">
                      <thead>
                        <tr>
                          <th>ID</th>
                          <th>Name</th>
                          <th>Email</th>
                          <th>Phone</th>
                          <th>Join Date</th>
                          <th>Plan</th>
                          <th>Expires</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {visible.length === 0 ? (
                          <tr><td colSpan={9} style={{ textAlign: 'center', color: '#888' }}>No members match the selected filters.</td></tr>
                        ) : visible.map((m) => (
                          <tr key={m.member_id}>
                            <td>{m.member_id}</td>
                            <td>{m.first_name} {m.last_name}</td>
                            <td>{m.email || '—'}</td>
                            <td>{m.phone_number || '—'}</td>
                            <td>{m.join_date ? new Date(m.join_date).toLocaleDateString() : '—'}</td>
                            <td>{m.plan_type || '—'}</td>
                            <td>{m.membership_end_date ? new Date(m.membership_end_date).toLocaleDateString() : '—'}</td>
                            <td>
                              <span style={{
                                backgroundColor: MEMBER_STATUS_COLORS[m.status] ?? '#6c757d',
                                color: '#fff', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.8rem',
                              }}>
                                {m.status}
                              </span>
                            </td>
                            <td>
                              {changingStatusFor === m.member_id ? (
                                <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                                  <select
                                    value={pendingStatus}
                                    onChange={(e) => setPendingStatus(e.target.value)}
                                    style={{ padding: '0.25rem', borderRadius: '4px', border: '1px solid #ccc', fontSize: '0.8rem' }}
                                  >
                                    <option value="ACTIVE">Active</option>
                                    <option value="INACTIVE">Inactive</option>
                                    <option value="SUSPENDED">Suspended</option>
                                  </select>
                                  <button
                                    className="btn"
                                    style={{ padding: '0.2rem 0.5rem', fontSize: '0.8rem' }}
                                    onClick={() => handleStatusUpdate(m.member_id)}
                                  >
                                    Save
                                  </button>
                                  <button
                                    className="btn btn-secondary"
                                    style={{ padding: '0.2rem 0.5rem', fontSize: '0.8rem' }}
                                    onClick={() => setChangingStatusFor(null)}
                                  >
                                    Cancel
                                  </button>
                                </div>
                              ) : (
                                <button
                                  className="btn btn-secondary"
                                  style={{ padding: '0.2rem 0.5rem', fontSize: '0.8rem' }}
                                  onClick={() => {
                                    setPendingStatus(m.status === 'Suspended' ? 'SUSPENDED' : m.status === 'Active' ? 'ACTIVE' : 'INACTIVE');
                                    setChangingStatusFor(m.member_id);
                                  }}
                                >
                                  Change Status
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  );
                })()}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
