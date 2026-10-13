import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  build: {
    manifest: true,
    sourcemap: false,
    cssCodeSplit: true,
    lib: { entry: __ENTRY__, formats: ['es'] },
    rolldownOptions: {
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
  },
});
