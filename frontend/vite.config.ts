import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/portfolio": "http://127.0.0.1:8000",
      "/rebalance": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000"
    }
  }
});

