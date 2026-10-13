import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  build: {
    manifest: true,
    sourcemap: false,
    cssCodeSplit: true,
    rolldownOptions: {
      input: __ENTRY__,
      // HostedPages imports mount from this entry; keep its public exports.
      preserveEntrySignatures: 'strict',
      output: {
        format: 'es',
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
  },
});
