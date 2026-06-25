const DEFAULT_API_BASE_URL = "https://chronexis-automated-time-table-generator.onrender.com";

export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim().replace(/\/+$/, "") ||
  DEFAULT_API_BASE_URL;

export const apiUrl = (path: string) => {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
};
