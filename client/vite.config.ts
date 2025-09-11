import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  
  server: {
    port: 8005,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3007',
        changeOrigin: true,
        secure: false
      }
    }
  },

  // 构建优化配置
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React核心库单独打包
          'react-vendor': ['react', 'react-dom'],
          // Ant Design组件库单独打包  
          'antd-vendor': ['antd', '@ant-design/icons', '@ant-design/charts'],
          // 图表库
          'charts-vendor': ['echarts', 'echarts-for-react'],
          // 工具库
          'utils-vendor': ['axios', 'dayjs', 'numeral'],
          // 动画库
          'animation-vendor': ['framer-motion']
        },
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') ?? [];
          if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(assetInfo.name ?? '')) {
            return `images/[name]-[hash][extname]`;
          }
          if (/\.(css|scss|less)$/i.test(assetInfo.name ?? '')) {
            return `css/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        }
      }
    },
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    chunkSizeWarningLimit: 1000
  },

  // 预构建优化
  optimizeDeps: {
    include: [
      'react',
      'react-dom', 
      'antd',
      '@ant-design/icons',
      'axios',
      'dayjs',
      'echarts'
    ]
  }
});
