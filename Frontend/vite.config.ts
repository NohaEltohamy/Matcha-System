import { defineConfig } from "vite";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    host: "::",
    port: 8080,
  },
  plugins: [],
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html'),
        demo: path.resolve(__dirname, 'public/demo.html'),
        login: path.resolve(__dirname, 'public/login.html'),
        signup: path.resolve(__dirname, 'public/signup.html'),
      }
    }
  },
  publicDir: 'public',
});
