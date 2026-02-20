import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  base: '/static/',
  plugins: [
    tailwindcss(),
  ],
  server: {
    // Indispensable pour que Django puisse accéder aux assets en mode dev
    host: 'localhost',
    port: 5173,
    strictPort: true,
    origin: 'http://localhost:5173',
  },
  build: {
    outDir: 'project/static/dist', // Destination pour Django
    assetsDir: '',
    manifest: true,        // Génère le manifest.json pour django-vite
    rollupOptions: {
      input: 'project/static/src/main.css', // Votre source
    },
  },
});