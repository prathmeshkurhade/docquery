import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_URL,
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const register = (email: string, password: string) =>
  api.post("/auth/register", { email, password });

export const login = (email: string, password: string) =>
  api.post("/auth/login", { email, password });

export const getMe = () => api.get("/auth/me");

// Documents
export const uploadDocument = (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/documents/upload", formData);
};

export const listDocuments = () => api.get("/documents/");

export const getDocument = (id: string) => api.get(`/documents/${id}`);

export const deleteDocument = (id: string) => api.delete(`/documents/${id}`);

// Query
export const queryDocuments = (question: string, documentId?: string) =>
  api.post("/query/", {
    question,
    document_id: documentId || null,
  });

export default api;
