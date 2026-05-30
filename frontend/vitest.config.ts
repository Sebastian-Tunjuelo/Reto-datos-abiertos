import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  plugins: [
    // Enable JSON imports in tests
    {
      name: 'json-loader',
      transform(code, id) {
        if (id.endsWith('.geojson') || id.endsWith('.json')) {
          return { code: `export default ${code}`, map: null };
        }
      },
    },
  ],
  test: {
    environment: 'node',
    globals: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
