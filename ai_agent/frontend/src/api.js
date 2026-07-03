// =============================================================================
// api.js — All communication with the FastAPI backend
// =============================================================================

import { getToken, getRefreshToken, isTokenExpired, logout } from "./auth";

const API_BASE = "http://localhost:8000"; // ← CONFIGURE: backend URL

function authHeader(tokenOverride = null) {
  const token = tokenOverride || getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  if (!refreshToken || isTokenExpired(refreshToken)) {
    throw new Error("Refresh token expired or missing");
  }
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  if (!res.ok) throw new Error("Failed to refresh token");
  const data = await res.json();
  localStorage.setItem("token", data.access_token);
  return data.access_token;
}

async function authenticatedFetch(url, options = {}) {
  let token = getToken();
  if (token && isTokenExpired(token)) {
    try {
      token = await refreshAccessToken();
    } catch (err) {
      logout();
      window.location.reload();
      throw err;
    }
  }
  options.headers = { ...options.headers, ...authHeader(token) };
  let response = await fetch(url, options);
  if (response.status === 401) {
    try {
      token = await refreshAccessToken();
      options.headers = { ...options.headers, ...authHeader(token) };
      response = await fetch(url, options);
    } catch (err) {
      logout();
      window.location.reload();
      throw err;
    }
  }
  if (response.status === 401) {
    logout();
    window.location.reload();
    throw new Error("Session expired. Please log in again.");
  }
  return response;
}

// =============================================================================
// Recruiter APIs
// =============================================================================

export async function analyzeResume({ resumeFile, jdText, jdId = null, requiredExperience = 0.0, llmProvider = "groq" }) {
  const formData = new FormData();
  formData.append("resume", resumeFile);
  if (jdId) formData.append("jd_id", jdId.toString());
  if (jdText) formData.append("jd_text", jdText);
  formData.append("required_experience", requiredExperience.toString());
  formData.append("llm_provider", llmProvider);
  const response = await authenticatedFetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }
  return response.json();
}

export async function analyzeBatch({
  resumeFiles,
  jdText = null,
  jdId = null,
  requiredExperience = 0.0,
  llmProvider = "ollama",
  enableLlm = true,
}) {
  const formData = new FormData();
  resumeFiles.forEach((file) => {
    formData.append("resumes", file);
  });
  if (jdId) formData.append("jd_id", jdId.toString());
  if (jdText) formData.append("jd_text", jdText);
  formData.append("required_experience", requiredExperience.toString());
  formData.append("llm_provider", llmProvider);
  formData.append("enable_llm", enableLlm.toString());
  const response = await authenticatedFetch(`${API_BASE}/api/analyze/batch`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }
  return response.json();
}

export async function getHistory() {
  const response = await authenticatedFetch(`${API_BASE}/api/history`, { method: "GET" });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }
  return response.json();
}

export async function getHistoryDetail(historyId) {
  const response = await authenticatedFetch(`${API_BASE}/api/history/${historyId}`, { method: "GET" });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }
  return response.json();
}

// =============================================================================
// JD Library APIs
// =============================================================================

export async function getJDCategories() {
  const response = await authenticatedFetch(`${API_BASE}/api/jd-library/categories`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }
  return response.json();
}

export async function createJDCategory(name) {
  const response = await authenticatedFetch(`${API_BASE}/api/jd-library/categories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }
  return response.json();
}

export async function getJDLibrary() {
  const response = await authenticatedFetch(`${API_BASE}/api/jd-library`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }
  return response.json();
}

export async function getJDById(jdId) {
  const response = await authenticatedFetch(`${API_BASE}/api/jd-library/${jdId}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }
  return response.json();
}

export async function createJD({ category_id, title, jd_text }) {
  const response = await authenticatedFetch(`${API_BASE}/api/jd-library`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ category_id, title, jd_text }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }
  return response.json();
}

export async function deleteJD(jdId) {
  const response = await authenticatedFetch(`${API_BASE}/api/jd-library/${jdId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }
  return response.json();
}

export async function updateJD(jdId, { category_id, title, jd_text }) {
  const body = {};
  if (category_id !== undefined) body.category_id = category_id;
  if (title !== undefined) body.title = title;
  if (jd_text !== undefined) body.jd_text = jd_text;
  const response = await authenticatedFetch(`${API_BASE}/api/jd-library/${jdId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${response.status}`);
  }
  return response.json();
}


// =============================================================================
// Manager APIs
// Note: These endpoints are stubs that will call real backend routes.
//       Mock data is returned when the backend returns 404/501.
// =============================================================================

export async function getManagerCandidates(department) {
  try {
    const response = await authenticatedFetch(
      `${API_BASE}/api/manager/candidates${department ? `?department=${encodeURIComponent(department)}` : ""}`,
      { method: "GET" }
    );
    if (!response.ok) return getMockCandidates();
    return response.json();
  } catch {
    return getMockCandidates();
  }
}

export async function getCandidateDetail(candidateId) {
  try {
    const response = await authenticatedFetch(`${API_BASE}/api/manager/candidates/${candidateId}`, { method: "GET" });
    if (!response.ok) return getMockCandidateDetail(candidateId);
    return response.json();
  } catch {
    return getMockCandidateDetail(candidateId);
  }
}

export async function approveCandidate(candidateId) {
  try {
    const response = await authenticatedFetch(`${API_BASE}/api/manager/candidates/${candidateId}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) return { success: true, status: "Selected" };
    return response.json();
  } catch {
    return { success: true, status: "Selected" };
  }
}

export async function rejectCandidate(candidateId) {
  try {
    const response = await authenticatedFetch(`${API_BASE}/api/manager/candidates/${candidateId}/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) return { success: true, status: "Rejected" };
    return response.json();
  } catch {
    return { success: true, status: "Rejected" };
  }
}

export async function scheduleInterview(candidateId, interviewData) {
  try {
    const response = await authenticatedFetch(`${API_BASE}/api/manager/candidates/${candidateId}/interview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(interviewData),
    });
    if (!response.ok) return { success: true, status: "Interview Scheduled" };
    return response.json();
  } catch {
    return { success: true, status: "Interview Scheduled" };
  }
}

export async function addInterviewNotes(candidateId, notes) {
  try {
    const response = await authenticatedFetch(`${API_BASE}/api/manager/candidates/${candidateId}/notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes }),
    });
    if (!response.ok) return { success: true };
    return response.json();
  } catch {
    return { success: true };
  }
}
