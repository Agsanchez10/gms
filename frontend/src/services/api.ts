import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatically attach staff_id query param to every request when logged in
apiClient.interceptors.request.use((config) => {
  const stored = localStorage.getItem('user');
  if (stored) {
    const user = JSON.parse(stored);
    if (user?.staff_id) {
      config.params = { ...config.params, staff_id: user.staff_id };
    }
  }
  return config;
});

// Member APIs
export const memberAPI = {
  list: (skip = 0, limit = 10) => apiClient.get('/members/', { params: { skip, limit } }),
  get: (memberId: number) => apiClient.get(`/members/${memberId}`),
  create: (data: any) => apiClient.post('/members/', data),
  update: (memberId: number, data: any) => apiClient.put(`/members/${memberId}`, data),
  delete: (memberId: number) => apiClient.delete(`/members/${memberId}`),
  updateStatus: (memberId: number, newStatus: string) =>
    apiClient.patch(`/members/${memberId}/status`, null, { params: { new_status: newStatus } }),
  getCurrentMembership: (memberId: number) => apiClient.get(`/members/${memberId}/current-membership/`),
};

// Staff APIs
export const staffAPI = {
  login: (email: string, password: string) => apiClient.post('/staff/login', { email, password }),
  register: (data: any) => apiClient.post('/staff/register', data),
  list: () => apiClient.get('/staff/'),
  get: (staffId: number) => apiClient.get(`/staff/${staffId}`),
  getMe: () => apiClient.get('/staff/me'),
};

// Class APIs
export const classAPI = {
  list: (skip = 0, limit = 10, trainerId?: number) =>
    apiClient.get('/classes/', { params: { skip, limit, trainer_id: trainerId } }),
  get: (classId: number) => apiClient.get(`/classes/${classId}`),
  create: (data: any) => apiClient.post('/classes/', data),
  update: (classId: number, data: any) => apiClient.put(`/classes/${classId}`, data),
  delete: (classId: number) => apiClient.delete(`/classes/${classId}`),
  enrollMember: (classId: number, memberId: number) =>
    apiClient.post(`/classes/${classId}/enroll/${memberId}`),
  removeMember: (classId: number, memberId: number) =>
    apiClient.delete(`/classes/${classId}/enroll/${memberId}`),
  checkinMember: (classId: number, memberId: number) =>
    apiClient.put(`/classes/${classId}/checkin/${memberId}`),
};

// Machine APIs
export const machineAPI = {
  list: (skip = 0, limit = 10, status?: string, category?: string) =>
    apiClient.get('/machines/', { params: { skip, limit, status_filter: status, category_filter: category } }),
  get: (machineId: number) => apiClient.get(`/machines/${machineId}`),
  create: (data: any) => apiClient.post('/machines/', data),
  update: (machineId: number, data: any) => apiClient.put(`/machines/${machineId}`, data),
  delete: (machineId: number) => apiClient.delete(`/machines/${machineId}`),
  getStatus: (machineId: number) => apiClient.get(`/machines/${machineId}/status`),
  updateStatus: (machineId: number, newStatus: string) =>
    apiClient.patch(`/machines/${machineId}/status`, null, { params: { new_status: newStatus } }),
};

// Machine Usage APIs
export const usageAPI = {
  startUsage: (machineId: number, memberId: number) =>
    apiClient.post(`/machines/${machineId}/start`, { member_id: memberId }),
  endUsage: (machineId: number, usageId: number) =>
    apiClient.put(`/machines/${machineId}/end/${usageId}`),
  getMachineHistory: (machineId: number, skip = 0, limit = 20) =>
    apiClient.get(`/machines/${machineId}/usage`, { params: { skip, limit } }),
  getMemberHistory: (memberId: number, skip = 0, limit = 20) =>
    apiClient.get(`/members/${memberId}/usage`, { params: { skip, limit } }),
  getMachineStats: (machineId: number, days = 30) =>
    apiClient.get(`/stats/machine/${machineId}`, { params: { days } }),
  getMemberStats: (memberId: number, days = 30) =>
    apiClient.get(`/stats/member/${memberId}`, { params: { days } }),
};

// Plan APIs
export const planAPI = {
  list: () => apiClient.get('/plans/'),
  get: (planId: number) => apiClient.get(`/plans/${planId}`),
  create: (data: any) => apiClient.post('/plans/', data),
  update: (planId: number, data: any) => apiClient.put(`/plans/${planId}`, data),
  delete: (planId: number) => apiClient.delete(`/plans/${planId}`),
};

// Membership APIs
export const membershipAPI = {
  enrollMember: (memberId: number, planId: number) =>
    apiClient.post(`/memberships/members/${memberId}/enroll`, { plan_id: planId }),
  getCurrentMembership: (memberId: number) =>
    apiClient.get(`/memberships/members/${memberId}/current`),
  renewMembership: (memberId: number, planId: number) =>
    apiClient.put(`/memberships/members/${memberId}/${planId}/renew`),
};

// Manager Analytics APIs
export const managerAPI = {
  getDashboardOverview: () => apiClient.get('/manager/dashboard/overview'),
  getMachineUsageAnalytics: (days = 30) =>
    apiClient.get('/manager/analytics/machine-usage', { params: { days } }),
  getClassEnrollmentAnalytics: () => apiClient.get('/manager/analytics/class-enrollment'),
  getMembershipStatusAnalytics: () => apiClient.get('/manager/analytics/membership-status'),
  getStaffRoleDistribution: () => apiClient.get('/manager/analytics/staff-roles'),
  getTopMembers: (limit = 10, days = 30) =>
    apiClient.get('/manager/analytics/top-members', { params: { limit, days } }),
};

// Trainer APIs
export const trainerAPI = {
  getMyClasses: () => apiClient.get('/trainer/my-classes'),
  getClassRoster: (classId: number) => apiClient.get(`/trainer/classes/${classId}/roster`),
  getClassAttendance: (classId: number) => apiClient.get(`/trainer/classes/${classId}/attendance`),
};

export default apiClient;
