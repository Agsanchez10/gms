import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { trainerAPI, classAPI, memberAPI } from '../services/api';

// ── Calendar helpers ────────────────────────────────────────────
const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const CLASS_TYPES = ['Yoga', 'Pilates', 'Cardio', 'Strength', 'HIIT', 'Zumba', 'Cycling', 'Spin', 'Boxing', 'Other'];

function startOfWeek(date: Date): Date {
  const d = new Date(date);
  d.setDate(d.getDate() - d.getDay());
  d.setHours(0, 0, 0, 0);
  return d;
}

function addDays(date: Date, n: number): Date {
  const d = new Date(date);
  d.setDate(d.getDate() + n);
  return d;
}

function fmt(date: Date): string {
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function fmtTime(dt: string | Date): string {
  const d = new Date(dt);
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
}

function sameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate();
}

// ── Empty form state ────────────────────────────────────────────
const EMPTY_FORM = { class_name: '', type: '', capacity: '', start_date: '', start_time_of_day: '08:00', duration_minutes: '60', description: '' };

const DURATION_OPTIONS = [15, 30, 45, 60, 75, 90, 105, 120, 150, 180];

// Generate every 15-minute slot for a full day (00:00 – 23:45)
const START_TIMES: { value: string; label: string }[] = [];
for (let h = 0; h < 24; h++) {
  for (const m of [0, 15, 30, 45]) {
    const hh = String(h).padStart(2, '0');
    const mm = String(m).padStart(2, '0');
    const value = `${hh}:${mm}`;
    const d = new Date(2000, 0, 1, h, m);
    const label = d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
    START_TIMES.push({ value, label });
  }
}

function pad(n: number) { return String(n).padStart(2, '0'); }

// Combines a date string (YYYY-MM-DD) and time string (HH:MM) into a datetime-local string
function combineDateTime(date: string, time: string): string {
  return `${date}T${time}`;
}

function addMinutes(datetimeLocal: string, minutes: number): string {
  const d = new Date(datetimeLocal);
  d.setMinutes(d.getMinutes() + minutes);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export default function TrainerDashboard() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('my-classes');
  const [classes, setClasses] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Members (for enroll search)
  const [members, setMembers] = useState<any[]>([]);
  const [membersError, setMembersError] = useState('');

  // Roster
  const [rosterClassId, setRosterClassId] = useState<number | null>(null);
  const [rosterClassName, setRosterClassName] = useState('');
  const [roster, setRoster] = useState<any[]>([]);
  const [rosterLoading, setRosterLoading] = useState(false);
  const [removeError, setRemoveError] = useState('');

  // Enroll
  const [enrollClassId, setEnrollClassId] = useState<number | null>(null);
  const [enrollMemberId, setEnrollMemberId] = useState<number | null>(null);
  const [enrollSearch, setEnrollSearch] = useState('');
  const [enrollResults, setEnrollResults] = useState<any[]>([]);
  const [enrollError, setEnrollError] = useState('');
  const [enrollSuccess, setEnrollSuccess] = useState('');
  const [enrollLoading, setEnrollLoading] = useState(false);

  // My Classes — sort & filter
  const [sortField, setSortField] = useState<'start_time' | 'class_name'>('start_time');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [filterType, setFilterType] = useState('');
  const [filterMonth, setFilterMonth] = useState('');

  // Calendar week navigation
  const [weekStart, setWeekStart] = useState<Date>(() => startOfWeek(new Date()));

  // Add class
  const [showAddClass, setShowAddClass] = useState(false);
  const [newClass, setNewClass] = useState({ ...EMPTY_FORM });
  const [addClassError, setAddClassError] = useState('');
  const [addClassLoading, setAddClassLoading] = useState(false);

  // Delete class
  const [deleteClassId, setDeleteClassId] = useState<number | null>(null);
  const [deleteClassName, setDeleteClassName] = useState('');
  const [deleteEnrolled, setDeleteEnrolled] = useState(0);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  useEffect(() => {
    loadClasses();
    memberAPI.list(0, 100)
      .then((r) => setMembers(r.data))
      .catch(() => setMembersError('Could not load members. Is the backend running?'));
  }, []);

  const loadClasses = async () => {
    setLoading(true);
    try {
      const res = await trainerAPI.getMyClasses();
      setClasses(res.data);
    } catch (error) {
      console.error('Error loading classes:', error);
    }
    setLoading(false);
  };

  const handleRemoveMember = async (memberId: number) => {
    if (!rosterClassId) return;
    setRemoveError('');
    try {
      await classAPI.removeMember(rosterClassId, memberId);
      setRoster((prev) => prev.filter((m) => m.member_id !== memberId));
      setClasses((prev) =>
        prev.map((c) =>
          c.class_id === rosterClassId ? { ...c, enrolled_count: c.enrolled_count - 1 } : c
        )
      );
    } catch (err: any) {
      setRemoveError(err.response?.data?.detail || 'Failed to remove member.');
    }
  };

  const openEnroll = (cls: any) => {
    if (enrollClassId === cls.class_id) {
      setEnrollClassId(null);
      return;
    }
    setEnrollClassId(cls.class_id);
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
    setEnrollResults(members.filter((m) => {
      return String(m.member_id) === q ||
        `${m.first_name} ${m.last_name}`.toLowerCase().includes(q) ||
        m.email?.toLowerCase().includes(q);
    }));
  };

  // Add class handlers
  const handleAddClass = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddClassError('');
    setAddClassLoading(true);
    try {
      await classAPI.create({
        class_name: newClass.class_name,
        type: newClass.type,
        capacity: parseInt(newClass.capacity, 10),
        start_time: combineDateTime(newClass.start_date, newClass.start_time_of_day),
        end_time: addMinutes(combineDateTime(newClass.start_date, newClass.start_time_of_day), parseInt(newClass.duration_minutes, 10)),
        description: newClass.description || null,
        trainer_id: user?.staff_id,
      });
      setShowAddClass(false);
      setNewClass({ ...EMPTY_FORM });
      await loadClasses();
    } catch (err: any) {
      setAddClassError(err.response?.data?.detail || 'Failed to create class.');
    } finally {
      setAddClassLoading(false);
    }
  };

  // Confirm-delete flow
  const promptDelete = (cls: any) => {
    setDeleteClassId(cls.class_id);
    setDeleteClassName(cls.class_name);
    setDeleteEnrolled(cls.member_count ?? cls.enrolled_count ?? 0);
    setDeleteError('');
  };

  const handleDeleteClass = async () => {
    if (!deleteClassId) return;
    setDeleteLoading(true);
    setDeleteError('');
    try {
      await classAPI.delete(deleteClassId);
      setClasses((prev) => prev.filter((c) => c.class_id !== deleteClassId));
      if (rosterClassId === deleteClassId) setRosterClassId(null);
      if (enrollClassId === deleteClassId) setEnrollClassId(null);
      setDeleteClassId(null);
    } catch (err: any) {
      setDeleteError(err.response?.data?.detail || 'Failed to delete class.');
    } finally {
      setDeleteLoading(false);
    }
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
      const res = await trainerAPI.getMyClasses();
      setClasses(res.data);
    } catch (err: any) {
      setEnrollError(err.response?.data?.detail || 'Enrollment failed.');
    } finally {
      setEnrollLoading(false);
    }
  };

  const openRoster = async (cls: any) => {
    if (rosterClassId === cls.class_id) {
      setRosterClassId(null);
      return;
    }
    setEnrollClassId(null);
    setRemoveError('');
    setRosterClassId(cls.class_id);
    setRosterClassName(cls.class_name);
    setRosterLoading(true);
    try {
      const res = await classAPI.get(cls.class_id);
      setRoster(res.data.members ?? []);
    } catch {
      setRoster([]);
    } finally {
      setRosterLoading(false);
    }
  };

  const handleLogout = () => {
    setUser(null);
    navigate('/login');
  };

  return (
    <div className="app-container">
      <nav className="navbar">
        <h1>Trainer Dashboard</h1>
        <div className="user-info">
          {user?.role === 'Manager' && (
            <button className="btn btn-secondary" onClick={() => navigate('/')} style={{ marginRight: '1rem' }}>
              ← Manager Dashboard
            </button>
          )}
          <span>{user?.first_name} {user?.last_name} ({user?.role})</span>
          <button className="logout-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      <div className="main-content">
        <div style={{ marginBottom: '2rem' }}>
          <button
            className={`btn ${tab === 'my-classes' ? '' : 'btn-secondary'}`}
            onClick={() => setTab('my-classes')}
          >
            My Classes
          </button>
          <button
            className={`btn ${tab === 'schedule' ? '' : 'btn-secondary'}`}
            onClick={() => setTab('schedule')}
            style={{ marginLeft: '0.5rem' }}
          >
            Schedule
          </button>
        </div>

        {tab === 'my-classes' && (
          <div className="card">
            <h2>My Classes</h2>

            {/* ── Sort & Filter controls ── */}
            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem', alignItems: 'center' }}>
              {/* Sort */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <label style={{ fontWeight: 600, fontSize: '0.9rem', whiteSpace: 'nowrap' }}>Sort by</label>
                <select
                  value={sortField}
                  onChange={(e) => setSortField(e.target.value as 'start_time' | 'class_name')}
                  style={{ padding: '0.35rem 0.5rem', borderRadius: '4px', border: '1px solid #ccc', fontSize: '0.9rem' }}
                >
                  <option value="start_time">Date</option>
                  <option value="class_name">Class Name</option>
                </select>
                <button
                  className="btn btn-secondary"
                  style={{ fontSize: '0.85rem', padding: '0.3rem 0.6rem' }}
                  title={sortDir === 'asc' ? 'Ascending' : 'Descending'}
                  onClick={() => setSortDir((d) => d === 'asc' ? 'desc' : 'asc')}
                >
                  {sortDir === 'asc' ? '↑ Asc' : '↓ Desc'}
                </button>
              </div>

              {/* Filter by Type */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <label style={{ fontWeight: 600, fontSize: '0.9rem', whiteSpace: 'nowrap' }}>Type</label>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  style={{ padding: '0.35rem 0.5rem', borderRadius: '4px', border: '1px solid #ccc', fontSize: '0.9rem' }}
                >
                  <option value="">All types</option>
                  {[...new Set(classes.map((c) => c.type))].sort().map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              {/* Filter by Month */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <label style={{ fontWeight: 600, fontSize: '0.9rem', whiteSpace: 'nowrap' }}>Month</label>
                <select
                  value={filterMonth}
                  onChange={(e) => setFilterMonth(e.target.value)}
                  style={{ padding: '0.35rem 0.5rem', borderRadius: '4px', border: '1px solid #ccc', fontSize: '0.9rem' }}
                >
                  <option value="">All months</option>
                  {[...new Set(classes.map((c) => {
                    const d = new Date(c.start_time);
                    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
                  }))].sort().map((ym) => {
                    const [y, m] = ym.split('-');
                    const label = new Date(Number(y), Number(m) - 1, 1).toLocaleString('en-US', { month: 'long', year: 'numeric' });
                    return <option key={ym} value={ym}>{label}</option>;
                  })}
                </select>
              </div>

              {(filterType || filterMonth) && (
                <button
                  className="btn btn-secondary"
                  style={{ fontSize: '0.85rem', padding: '0.3rem 0.6rem' }}
                  onClick={() => { setFilterType(''); setFilterMonth(''); }}
                >
                  ✕ Clear filters
                </button>
              )}
            </div>

            {loading ? (
              <p>Loading...</p>
            ) : classes.length === 0 ? (
              <p>No classes assigned to you yet.</p>
            ) : (() => {
              const filtered = classes
                .filter((c) => !filterType || c.type === filterType)
                .filter((c) => {
                  if (!filterMonth) return true;
                  const d = new Date(c.start_time);
                  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}` === filterMonth;
                })
                .sort((a, b) => {
                  const av = sortField === 'start_time' ? new Date(a.start_time).getTime() : a.class_name.toLowerCase();
                  const bv = sortField === 'start_time' ? new Date(b.start_time).getTime() : b.class_name.toLowerCase();
                  if (av < bv) return sortDir === 'asc' ? -1 : 1;
                  if (av > bv) return sortDir === 'asc' ? 1 : -1;
                  return 0;
                });
              return filtered.length === 0 ? (
                <p style={{ color: '#888' }}>No classes match the current filters.</p>
              ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Class Name</th>
                    <th>Type</th>
                    <th>Capacity</th>
                    <th>Enrolled</th>
                    <th>Start Time</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((cls) => (
                    <tr key={cls.class_id}>
                      <td>{cls.class_name}</td>
                      <td>{cls.type}</td>
                      <td>{cls.capacity}</td>
                      <td>{cls.enrolled_count}</td>
                      <td>{new Date(cls.start_time).toLocaleString()}</td>
                      <td style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                        <button
                          className="btn"
                          style={{ fontSize: '0.85rem' }}
                          onClick={() => openRoster(cls)}
                        >
                          {rosterClassId === cls.class_id ? 'Hide Roster' : 'View Roster'}
                        </button>
                        <button
                          className="btn btn-secondary"
                          style={{ fontSize: '0.85rem' }}
                          onClick={() => openEnroll(cls)}
                        >
                          {enrollClassId === cls.class_id ? 'Cancel Enroll' : 'Enroll Member'}
                        </button>
                        <button
                          className="btn"
                          style={{ fontSize: '0.85rem', background: '#ef4444', color: '#fff' }}
                          onClick={() => promptDelete(cls)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              );
            })()}

            {enrollSuccess && (
              <div className="alert alert-success" style={{ marginTop: '1rem' }}>{enrollSuccess}</div>
            )}

            {enrollClassId != null && (
              <div style={{ background: '#f0f7ff', border: '1px solid #b8d9f8', borderRadius: '6px', padding: '1.25rem', marginTop: '1.5rem' }}>
                <h3 style={{ marginTop: 0 }}>
                  Enroll Member — {classes.find((c) => c.class_id === enrollClassId)?.class_name}
                </h3>
                {enrollError && <div className="alert alert-error">{enrollError}</div>}
                <form onSubmit={handleEnrollSubmit}>
                  {membersError && <div className="alert alert-error" style={{ marginBottom: '0.75rem' }}>{membersError}</div>}
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
                            padding: '0.6rem 1rem', cursor: 'pointer', borderBottom: '1px solid #f0f0f0',
                            backgroundColor: enrollMemberId === m.member_id ? '#e8f4fd' : 'transparent',
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
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
                      {enrollLoading ? 'Enrolling…' : 'Enroll'}
                    </button>
                    <button type="button" className="btn btn-secondary" onClick={() => setEnrollClassId(null)}>Cancel</button>
                  </div>
                </form>
              </div>
            )}

            {rosterClassId != null && (
              <div style={{ marginTop: '1.5rem', borderTop: '1px solid #ddd', paddingTop: '1rem' }}>
                <h3 style={{ marginTop: 0 }}>Roster — {rosterClassName}</h3>
                {removeError && <div className="alert alert-error" style={{ marginBottom: '0.75rem' }}>{removeError}</div>}
                {rosterLoading ? (
                  <p>Loading roster…</p>
                ) : roster.length === 0 ? (
                  <p>No members enrolled.</p>
                ) : (
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Phone</th>
                        <th>Status</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {roster.map((m) => (
                        <tr key={m.member_id}>
                          <td>{m.first_name} {m.last_name}</td>
                          <td>{m.email}</td>
                          <td>{m.phone_number}</td>
                          <td>
                            <span style={{
                              background: m.status === 'Active' ? '#22c55e' : '#94a3b8',
                              color: '#fff', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.85rem',
                            }}>
                              {m.status}
                            </span>
                          </td>
                          <td>
                            <button
                              className="btn btn-secondary"
                              style={{ fontSize: '0.85rem', background: '#ef4444', color: '#fff' }}
                              onClick={() => handleRemoveMember(m.member_id)}
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
          </div>
        )}

        {tab === 'schedule' && (
          <div className="card">
            {/* ── Calendar header ── */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ margin: 0 }}>Class Schedule</h2>
              <button
                className="btn"
                style={{ background: '#22c55e', color: '#fff' }}
                onClick={() => { setShowAddClass(true); setAddClassError(''); setNewClass({ ...EMPTY_FORM }); }}
              >
                + Add Class
              </button>
            </div>

            {/* ── Week navigation ── */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
              <button className="btn btn-secondary" onClick={() => setWeekStart((w) => addDays(w, -7))}>‹ Prev</button>
              <span style={{ fontWeight: 600, minWidth: '160px', textAlign: 'center' }}>
                {fmt(weekStart)} – {fmt(addDays(weekStart, 6))}
              </span>
              <button className="btn btn-secondary" onClick={() => setWeekStart((w) => addDays(w, 7))}>Next ›</button>
              <button
                className="btn btn-secondary"
                style={{ fontSize: '0.85rem' }}
                onClick={() => setWeekStart(startOfWeek(new Date()))}
              >
                Today
              </button>

              {/* ── Quick week jump ── */}
              <select
                style={{ padding: '0.4rem 0.6rem', borderRadius: '4px', border: '1px solid #ccc', fontSize: '0.9rem', cursor: 'pointer' }}
                value=""
                onChange={(e) => {
                  if (e.target.value) setWeekStart(new Date(e.target.value));
                }}
              >
                <option value="">Jump to week…</option>
                {Array.from({ length: 26 }, (_, i) => {
                  const ws = startOfWeek(addDays(startOfWeek(new Date()), i * 7));
                  const we = addDays(ws, 6);
                  const isCurrentWeek = ws.getTime() === startOfWeek(new Date()).getTime();
                  return (
                    <option key={i} value={ws.toISOString()}>
                      {isCurrentWeek ? '★ ' : ''}{fmt(ws)} – {fmt(we)}
                    </option>
                  );
                })}
              </select>
            </div>

            {loading ? <p>Loading…</p> : (
              /* ── 7-column calendar grid ── */
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '0.5rem', overflowX: 'auto' }}>
                {DAYS.map((dayName, i) => {
                  const dayDate = addDays(weekStart, i);
                  const isToday = sameDay(dayDate, new Date());
                  const dayClasses = classes
                    .filter((cls) => sameDay(new Date(cls.start_time), dayDate))
                    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime());

                  return (
                    <div key={i} style={{ minWidth: '120px' }}>
                      {/* Day header */}
                      <div style={{
                        textAlign: 'center', padding: '0.4rem 0.25rem', borderRadius: '6px 6px 0 0',
                        background: isToday ? '#007bff' : '#e9ecef',
                        color: isToday ? '#fff' : '#333', fontWeight: 600, fontSize: '0.8rem',
                        borderBottom: '2px solid ' + (isToday ? '#0056b3' : '#dee2e6'),
                      }}>
                        <div>{dayName}</div>
                        <div style={{ fontSize: '1rem' }}>{dayDate.getDate()}</div>
                      </div>

                      {/* Class cards */}
                      <div style={{
                        minHeight: '160px', background: isToday ? '#f0f7ff' : '#fafafa',
                        border: '1px solid #dee2e6', borderTop: 'none', borderRadius: '0 0 6px 6px',
                        padding: '0.35rem', display: 'flex', flexDirection: 'column', gap: '0.35rem',
                      }}>
                        {dayClasses.length === 0 && (
                          <p style={{ color: '#aaa', fontSize: '0.75rem', textAlign: 'center', marginTop: '0.75rem' }}>—</p>
                        )}
                        {dayClasses.map((cls) => (
                          <div key={cls.class_id} style={{
                            background: '#fff', border: '1px solid #b8d9f8', borderRadius: '5px',
                            padding: '0.4rem 0.5rem', fontSize: '0.78rem', position: 'relative',
                          }}>
                            <div style={{ fontWeight: 700, color: '#1a56db', marginBottom: '0.15rem', paddingRight: '1.2rem' }}>
                              {cls.class_name}
                            </div>
                            <div style={{ color: '#555' }}>{cls.type}</div>
                            <div style={{ color: '#666' }}>{fmtTime(cls.start_time)} – {fmtTime(cls.end_time)}</div>
                            <div style={{ color: '#888' }}>
                              {cls.member_count ?? cls.enrolled_count ?? 0}/{cls.capacity}
                            </div>
                            <button
                              title="Delete class"
                              onClick={() => promptDelete(cls)}
                              style={{
                                position: 'absolute', top: '0.3rem', right: '0.3rem',
                                background: 'transparent', border: 'none', cursor: 'pointer',
                                color: '#ef4444', fontWeight: 700, fontSize: '0.9rem', lineHeight: 1, padding: 0,
                              }}
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Add Class Modal ── */}
      {showAddClass && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div style={{
            background: '#fff', borderRadius: '10px', padding: '2rem', width: '100%', maxWidth: '500px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.2)', maxHeight: '90vh', overflowY: 'auto',
          }}>
            <h2 style={{ marginTop: 0 }}>Add New Class</h2>
            {addClassError && <div className="alert alert-error" style={{ marginBottom: '1rem' }}>{addClassError}</div>}
            <form onSubmit={handleAddClass}>
              <div className="form-group">
                <label>Class Name *</label>
                <input type="text" required value={newClass.class_name}
                  onChange={(e) => setNewClass((p) => ({ ...p, class_name: e.target.value }))}
                  placeholder="e.g. Morning Yoga" />
              </div>
              <div className="form-group">
                <label>Type *</label>
                <select required value={newClass.type}
                  onChange={(e) => setNewClass((p) => ({ ...p, type: e.target.value }))}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}>
                  <option value="">Select type…</option>
                  {CLASS_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Capacity *</label>
                <input type="number" required min={1} value={newClass.capacity}
                  onChange={(e) => setNewClass((p) => ({ ...p, capacity: e.target.value }))}
                  placeholder="e.g. 20" />
              </div>
              <div className="form-group">
                <label>Date *</label>
                <input type="date" required value={newClass.start_date}
                  onChange={(e) => setNewClass((p) => ({ ...p, start_date: e.target.value }))} />
              </div>
              <div className="form-group">
                <label>Start Time *</label>
                <select required value={newClass.start_time_of_day}
                  onChange={(e) => setNewClass((p) => ({ ...p, start_time_of_day: e.target.value }))}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}>
                  {START_TIMES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Duration *</label>
                <select required value={newClass.duration_minutes}
                  onChange={(e) => setNewClass((p) => ({ ...p, duration_minutes: e.target.value }))}
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}>
                  {DURATION_OPTIONS.map((m) => (
                    <option key={m} value={m}>
                      {m < 60 ? `${m} min` : m % 60 === 0 ? `${m / 60} hr` : `${Math.floor(m / 60)} hr ${m % 60} min`}
                    </option>
                  ))}
                </select>
                {newClass.start_date && (
                  <small style={{ color: '#555', marginTop: '0.25rem', display: 'block' }}>
                    Ends at {new Date(addMinutes(combineDateTime(newClass.start_date, newClass.start_time_of_day), parseInt(newClass.duration_minutes, 10))).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}
                  </small>
                )}
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea rows={2} value={newClass.description}
                  onChange={(e) => setNewClass((p) => ({ ...p, description: e.target.value }))}
                  placeholder="Optional description…"
                  style={{ width: '100%', padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc', resize: 'vertical' }} />
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                <button type="submit" className="btn" disabled={addClassLoading}>
                  {addClassLoading ? 'Saving…' : 'Create Class'}
                </button>
                <button type="button" className="btn btn-secondary"
                  onClick={() => { setShowAddClass(false); setNewClass({ ...EMPTY_FORM }); }}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Delete Confirmation Modal ── */}
      {deleteClassId != null && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
          <div style={{
            background: '#fff', borderRadius: '10px', padding: '2rem', width: '100%', maxWidth: '420px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
          }}>
            <h2 style={{ marginTop: 0, color: '#ef4444' }}>Delete Class</h2>
            <p>
              Are you sure you want to delete <strong>{deleteClassName}</strong>?
            </p>
            {deleteEnrolled > 0 && (
              <p style={{ color: '#b45309', background: '#fef3c7', padding: '0.75rem', borderRadius: '6px' }}>
                ⚠ This will remove all <strong>{deleteEnrolled}</strong> enrolled member{deleteEnrolled !== 1 ? 's' : ''} from the class.
              </p>
            )}
            {deleteError && <div className="alert alert-error" style={{ marginBottom: '1rem' }}>{deleteError}</div>}
            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
              <button
                className="btn"
                style={{ background: '#ef4444', color: '#fff' }}
                disabled={deleteLoading}
                onClick={handleDeleteClass}
              >
                {deleteLoading ? 'Deleting…' : 'Delete Class'}
              </button>
              <button
                className="btn btn-secondary"
                disabled={deleteLoading}
                onClick={() => { setDeleteClassId(null); setDeleteError(''); }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
