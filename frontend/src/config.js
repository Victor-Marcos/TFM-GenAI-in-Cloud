// URL base del backend.
// - En desarrollo (npm run dev) se lee de .env.development -> http://localhost:8000
// - En producción no existe la variable, así que se usa '/api' (Nginx lo redirige al backend)
export const API_URL = import.meta.env.VITE_API_URL || '/api'