import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    // 按需自动导入 Element Plus 组件与函数（ElMessage 等），减小打包体积
    AutoImport({
      resolvers: [ElementPlusResolver()],
      dts: false // 不生成类型声明文件，避免沙箱环境写文件权限问题
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: false
    })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    // 沙箱环境下 rmSync 被接管（genie-trash）会超时，关闭自动清空目录
    emptyOutDir: false
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8342',
        changeOrigin: true
      }
    }
  }
})
