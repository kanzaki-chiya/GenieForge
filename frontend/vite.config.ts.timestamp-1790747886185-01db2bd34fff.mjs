// vite.config.ts
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "file:///D:/code/GenieForge/frontend/node_modules/vite/dist/node/index.js";
import vue from "file:///D:/code/GenieForge/frontend/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import AutoImport from "file:///D:/code/GenieForge/frontend/node_modules/unplugin-auto-import/dist/vite.mjs";
import Components from "file:///D:/code/GenieForge/frontend/node_modules/unplugin-vue-components/dist/vite.mjs";
import { ElementPlusResolver } from "file:///D:/code/GenieForge/frontend/node_modules/unplugin-vue-components/dist/resolvers.mjs";
var __vite_injected_original_import_meta_url = "file:///D:/code/GenieForge/frontend/vite.config.ts";
var vite_config_default = defineConfig({
  plugins: [
    vue(),
    // 按需自动导入 Element Plus 组件与函数（ElMessage 等），减小打包体积
    AutoImport({
      resolvers: [ElementPlusResolver()],
      dts: false
      // 不生成类型声明文件，避免沙箱环境写文件权限问题
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: false
    })
  ],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", __vite_injected_original_import_meta_url))
    }
  },
  build: {
    // 沙箱环境下 rmSync 被接管（genie-trash）会超时，关闭自动清空目录
    emptyOutDir: false
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8342",
        changeOrigin: true
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJEOlxcXFxjb2RlXFxcXEdlbmllRm9yZ2VcXFxcZnJvbnRlbmRcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfZmlsZW5hbWUgPSBcIkQ6XFxcXGNvZGVcXFxcR2VuaWVGb3JnZVxcXFxmcm9udGVuZFxcXFx2aXRlLmNvbmZpZy50c1wiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9pbXBvcnRfbWV0YV91cmwgPSBcImZpbGU6Ly8vRDovY29kZS9HZW5pZUZvcmdlL2Zyb250ZW5kL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZmlsZVVSTFRvUGF0aCwgVVJMIH0gZnJvbSAnbm9kZTp1cmwnXG5pbXBvcnQgeyBkZWZpbmVDb25maWcgfSBmcm9tICd2aXRlJ1xuaW1wb3J0IHZ1ZSBmcm9tICdAdml0ZWpzL3BsdWdpbi12dWUnXG5pbXBvcnQgQXV0b0ltcG9ydCBmcm9tICd1bnBsdWdpbi1hdXRvLWltcG9ydC92aXRlJ1xuaW1wb3J0IENvbXBvbmVudHMgZnJvbSAndW5wbHVnaW4tdnVlLWNvbXBvbmVudHMvdml0ZSdcbmltcG9ydCB7IEVsZW1lbnRQbHVzUmVzb2x2ZXIgfSBmcm9tICd1bnBsdWdpbi12dWUtY29tcG9uZW50cy9yZXNvbHZlcnMnXG5cbmV4cG9ydCBkZWZhdWx0IGRlZmluZUNvbmZpZyh7XG4gIHBsdWdpbnM6IFtcbiAgICB2dWUoKSxcbiAgICAvLyBcdTYzMDlcdTk3MDBcdTgxRUFcdTUyQThcdTVCRkNcdTUxNjUgRWxlbWVudCBQbHVzIFx1N0VDNFx1NEVGNlx1NEUwRVx1NTFGRFx1NjU3MFx1RkYwOEVsTWVzc2FnZSBcdTdCNDlcdUZGMDlcdUZGMENcdTUxQ0ZcdTVDMEZcdTYyNTNcdTUzMDVcdTRGNTNcdTc5RUZcbiAgICBBdXRvSW1wb3J0KHtcbiAgICAgIHJlc29sdmVyczogW0VsZW1lbnRQbHVzUmVzb2x2ZXIoKV0sXG4gICAgICBkdHM6IGZhbHNlIC8vIFx1NEUwRFx1NzUxRlx1NjIxMFx1N0M3Qlx1NTc4Qlx1NThGMFx1NjYwRVx1NjU4N1x1NEVGNlx1RkYwQ1x1OTA3Rlx1NTE0RFx1NkM5OVx1N0JCMVx1NzNBRlx1NTg4M1x1NTE5OVx1NjU4N1x1NEVGNlx1Njc0M1x1OTY1MFx1OTVFRVx1OTg5OFxuICAgIH0pLFxuICAgIENvbXBvbmVudHMoe1xuICAgICAgcmVzb2x2ZXJzOiBbRWxlbWVudFBsdXNSZXNvbHZlcigpXSxcbiAgICAgIGR0czogZmFsc2VcbiAgICB9KVxuICBdLFxuICByZXNvbHZlOiB7XG4gICAgYWxpYXM6IHtcbiAgICAgICdAJzogZmlsZVVSTFRvUGF0aChuZXcgVVJMKCcuL3NyYycsIGltcG9ydC5tZXRhLnVybCkpXG4gICAgfVxuICB9LFxuICBidWlsZDoge1xuICAgIC8vIFx1NkM5OVx1N0JCMVx1NzNBRlx1NTg4M1x1NEUwQiBybVN5bmMgXHU4OEFCXHU2M0E1XHU3QkExXHVGRjA4Z2VuaWUtdHJhc2hcdUZGMDlcdTRGMUFcdThEODVcdTY1RjZcdUZGMENcdTUxNzNcdTk1RURcdTgxRUFcdTUyQThcdTZFMDVcdTdBN0FcdTc2RUVcdTVGNTVcbiAgICBlbXB0eU91dERpcjogZmFsc2VcbiAgfSxcbiAgc2VydmVyOiB7XG4gICAgcG9ydDogNTE3MyxcbiAgICBwcm94eToge1xuICAgICAgJy9hcGknOiB7XG4gICAgICAgIHRhcmdldDogJ2h0dHA6Ly8xMjcuMC4wLjE6ODM0MicsXG4gICAgICAgIGNoYW5nZU9yaWdpbjogdHJ1ZVxuICAgICAgfVxuICAgIH1cbiAgfVxufSlcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBMlEsU0FBUyxlQUFlLFdBQVc7QUFDOVMsU0FBUyxvQkFBb0I7QUFDN0IsT0FBTyxTQUFTO0FBQ2hCLE9BQU8sZ0JBQWdCO0FBQ3ZCLE9BQU8sZ0JBQWdCO0FBQ3ZCLFNBQVMsMkJBQTJCO0FBTGlJLElBQU0sMkNBQTJDO0FBT3ROLElBQU8sc0JBQVEsYUFBYTtBQUFBLEVBQzFCLFNBQVM7QUFBQSxJQUNQLElBQUk7QUFBQTtBQUFBLElBRUosV0FBVztBQUFBLE1BQ1QsV0FBVyxDQUFDLG9CQUFvQixDQUFDO0FBQUEsTUFDakMsS0FBSztBQUFBO0FBQUEsSUFDUCxDQUFDO0FBQUEsSUFDRCxXQUFXO0FBQUEsTUFDVCxXQUFXLENBQUMsb0JBQW9CLENBQUM7QUFBQSxNQUNqQyxLQUFLO0FBQUEsSUFDUCxDQUFDO0FBQUEsRUFDSDtBQUFBLEVBQ0EsU0FBUztBQUFBLElBQ1AsT0FBTztBQUFBLE1BQ0wsS0FBSyxjQUFjLElBQUksSUFBSSxTQUFTLHdDQUFlLENBQUM7QUFBQSxJQUN0RDtBQUFBLEVBQ0Y7QUFBQSxFQUNBLE9BQU87QUFBQTtBQUFBLElBRUwsYUFBYTtBQUFBLEVBQ2Y7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLE9BQU87QUFBQSxNQUNMLFFBQVE7QUFBQSxRQUNOLFFBQVE7QUFBQSxRQUNSLGNBQWM7QUFBQSxNQUNoQjtBQUFBLElBQ0Y7QUFBQSxFQUNGO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
