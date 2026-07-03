const API = "http://localhost:8000";

/**
 * Login with email and password (recruiter role)
 */
export async function login(email, password) {
    const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Invalid credentials");
    }
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    localStorage.setItem("email", email);
    localStorage.setItem("role", "recruiter");
    return data;
}

/**
 * Login as Hiring Manager
 */
export async function managerLogin(email, password) {
    // We hit the same auth endpoint but store role as "manager"
    // When backend role-awareness is added, swap this endpoint to /auth/manager-login
    const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Invalid credentials");
    }
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    localStorage.setItem("email", email);
    localStorage.setItem("role", "manager");
    return data;
}

/**
 * Register with email and password (recruiter)
 */
export async function signup(email, password) {
    const res = await fetch(`${API}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Registration failed");
    }
    return res.json();
}

/**
 * Register as Hiring Manager
 */
export async function managerSignup(email, password, name, department) {
    const res = await fetch(`${API}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name, department, role: "manager" })
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Manager registration failed");
    }
    return res.json();
}

export function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("email");
    localStorage.removeItem("role");
    localStorage.removeItem("managerName");
    localStorage.removeItem("managerDepartment");
}

export function getToken() {
    return localStorage.getItem("token");
}

export function getRefreshToken() {
    return localStorage.getItem("refresh_token");
}

export const isTokenExpired = (token) => {
    if (!token) return true;
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.exp * 1000 < Date.now();
    } catch (e) {
        return true;
    }
};

export function isLoggedIn() {
    const token = getToken();
    const refreshToken = getRefreshToken();
    if (token && !isTokenExpired(token)) return true;
    if (refreshToken && !isTokenExpired(refreshToken)) return true;
    return false;
}

export function getUserEmail() {
    return localStorage.getItem("email") || "";
}

export function getUserRole() {
    return localStorage.getItem("role") || "recruiter";
}

export function isManager() {
    return getUserRole() === "manager";
}

export function isRecruiter() {
    return getUserRole() === "recruiter";
}
