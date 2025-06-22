// @ts-ignore - types are provided via devDependencies once installed
import { defineConfig } from "vite";
// @ts-ignore - types are provided via devDependencies once installed
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy backend API during development
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
      },
    },
  },
}); 