import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// 性能优化的 Vite 配置
export default defineConfig({
  plugins: [react()],
  
  // 开发服务器配置
  server: {
    port: 8006,
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
    // 启用代码分割
    rollupOptions: {
      output: {
        // 手动分包策略
        manualChunks: {
          // React核心库单独打包
          'react-vendor': ['react', 'react-dom'],
          
          // Ant Design组件库单独打包  
          'antd-vendor': ['antd', '@ant-design/icons', '@ant-design/charts'],
          
          // 路由和状态管理
          'app-vendor': ['react-router-dom', 'react-redux', '@reduxjs/toolkit'],
          
          // 工具库
          'utils-vendor': ['axios', 'dayjs', 'echarts', 'echarts-for-react'],
          
          // 动效库
          'animation-vendor': ['framer-motion']
        },
        
        // 资源文件命名
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') ?? [];
          const extType = info[info.length - 1];
          if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(assetInfo.name ?? '')) {
            return `images/[name]-[hash][extname]`;
          }
          if (/\.(css|scss|less)$/i.test(assetInfo.name ?? '')) {
            return `css/[name]-[hash][extname]`;
          }
          if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name ?? '')) {
            return `fonts/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        }
      }
    },
    
    // 压缩配置
    minify: 'terser',
    terserOptions: {
      compress: {
        // 移除 console.log
        drop_console: true,
        // 移除 debugger
        drop_debugger: true,
        // 移除无用代码
        pure_funcs: ['console.log']
      }
    },
    
    // 设置chunk大小警告阈值
    chunkSizeWarningLimit: 1000,
    
    // 启用CSS代码分割
    cssCodeSplit: true
  },

  // 预构建优化
  optimizeDeps: {
    // 预构建包含的依赖
    include: [
      'react',
      'react-dom',
      'antd',
      '@ant-design/icons',
      'axios',
      'dayjs'
    ],
    
    // 排除预构建的包
    exclude: []
  },

  // 解析配置
  resolve: {
    // 路径别名
    alias: {
      '@': '/src',
      '@components': '/src/components',
      '@pages': '/src/pages', 
      '@utils': '/src/utils',
      '@types': '/src/types',
      '@shared': '/shared'
    }
  },

  // CSS预处理器配置
  css: {
    // CSS模块化配置
    modules: {
      // 生成的类名格式
      generateScopedName: '[name]__[local]___[hash:base64:5]'
    },
    
    // 预处理器选项
    preprocessorOptions: {
      less: {
        // Ant Design主题定制
        modifyVars: {
          // 可以在这里定制Ant Design主题色
        },
        javascriptEnabled: true
      }
    }
  },

  // 预览服务器配置
  preview: {
    port: 8006,
    host: true
  }
});