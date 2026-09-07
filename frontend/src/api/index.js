import api from './axios'

export const authAPI = {
  login:       (email, password)  => api.post('/auth/login/',        { email, password }),
  logout:      ()                 => api.post('/auth/logout/',        {}),
  refresh:     (refresh)          => api.post('/auth/refresh/',       { refresh }),
  me:          ()                 => api.get('/auth/me/'),
  tenants:     ()                 => api.get('/auth/tenants/'),
  register:    (data)             => api.post('/auth/register/',      data),
  googleLogin: (credential)       => api.post('/auth/google/',        { credential }),
}

export const alertsAPI = {
  list:          (params) => api.get('/detection/alerts/',     { params }),
  detail:        (id)     => api.get(`/detection/alerts/${id}/`),
  updateStatus:  (id, data) => api.patch(`/detection/alerts/${id}/`, data),
  escalate:      (id, data) => api.post(`/detection/alerts/${id}/escalate/`, data),
  triggerPlaybook: (id, data) => api.post(`/detection/alerts/${id}/trigger-playbook/`, data),
}

export const incidentsAPI = {
  list:   (params) => api.get('/detection/incidents/', { params }),
  detail: (id)     => api.get(`/detection/incidents/${id}/`),
  create: (data)   => api.post('/detection/incidents/', data),
  update: (id, data) => api.patch(`/detection/incidents/${id}/`, data),
}

export const networkEventsAPI = {
  list:       (params) => api.get('/ingestion/network-events/', { params }),
  detail:     (id)     => api.get(`/ingestion/network-events/${id}/`),
  verifyHash: (id)     => api.get(`/ingestion/network-events/${id}/verify-hash/`),
}

export const playbooksAPI = {
  list:    (params) => api.get('/detection/playbooks/', { params }),
  detail:  (id)     => api.get(`/detection/playbooks/${id}/`),
  create:  (data)   => api.post('/detection/playbooks/', data),
  update:  (id, d)  => api.patch(`/detection/playbooks/${id}/`, d),
  delete:  (id)     => api.delete(`/detection/playbooks/${id}/`),
  execute: (id, target_ip, dry_run = false) => api.post(`/detection/playbooks/${id}/execute/`, { target_ip, dry_run }),
}

export const blocklistAPI = {
  list:   (params) => api.get('/detection/blocklist/', { params }),
  add:    (data)   => api.post('/detection/blocklist/', data),
  remove: (id)     => api.delete(`/detection/blocklist/${id}/`),
}

export const complianceReportsAPI = {
  list:   (params) => api.get('/detection/compliance-reports/', { params }),
  detail: (id)     => api.get(`/detection/compliance-reports/${id}/`),
  create: (data)   => api.post('/detection/compliance-reports/', data),
  update: (id, d)  => api.patch(`/detection/compliance-reports/${id}/`, d),
  delete: (id)     => api.delete(`/detection/compliance-reports/${id}/`),
}


export const forensicsAPI = {
  // Cases
  listCases:    (p)   => api.get('/forensics/cases/', { params: p }),
  getCase:      (id)  => api.get(`/forensics/cases/${id}/`),
  createCase:   (d)   => api.post('/forensics/cases/', d),
  updateCase:   (id, d) => api.patch(`/forensics/cases/${id}/`, d),
  caseTimeline: (id)  => api.get(`/forensics/cases/${id}/timeline/`),
  caseEvidence: (id)  => api.get(`/forensics/cases/${id}/evidence/`),
  // Evidence
  uploadEvidence: (formData) => api.post('/forensics/evidence/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  verifyEvidence: (id) => api.get(`/forensics/evidence/${id}/verify/`),
  custodyTrail:   (id) => api.get(`/forensics/evidence/${id}/custody/`),
  // Timeline events
  addTimelineEvent: (d) => api.post('/forensics/timeline/', d),
}

export const mlAPI = {
  stats: () => api.get('/detection/ml/stats/'),
}

export const ingestionAPI = {
  syncWazuh: () => api.post('/ingestion/wazuh/sync/'),
  syncLogs:  (p) => api.get('/ingestion/sync-logs/', { params: p }),
}

export const assetsAPI = {
  list:   (params) => api.get('/assets/', { params }),
  detail: (id)     => api.get(`/assets/${id}/`),
  create: (data)   => api.post('/assets/', data),
  update: (id, d)  => api.put(`/assets/${id}/`, d),
  delete: (id)     => api.delete(`/assets/${id}/`),
}

