import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],

  // 开发环境使用根路径，生产环境使用 /app 子路径
  base: process.env.NODE_ENV === 'production' ? '/app' : '/',

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      'shared': path.resolve(__dirname, '../shared')
    }
  },

  server: {
    port: 8005,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3007',
        changeOrigin: true,
        secure: false,
        pathRewrite: {
          '^/api': '/api'  // 保留完整的 /api/v1 前缀
        }
      }
    }
  },

  preview: {
    port: 8005,
    host: true,
    allowedHosts: ['localhost', '127.0.0.1', 'qwquant.com', 'www.qwquant.com', '82.157.28.35'],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3007',
        changeOrigin: true,
        secure: false,
        pathRewrite: {
          '^/api': '/api'  // 保留完整的 /api/v1 前缀
        }
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
          'utils-vendor': ['dayjs', 'numeral'],
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
