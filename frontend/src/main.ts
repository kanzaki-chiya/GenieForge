import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElLoading } from 'element-plus'
// 函数式组件（ElMessage / ElMessageBox）与指令（v-loading）按需引入样式
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/es/components/loading/style/css'
import App from './App.vue'
import router from './router'

// 模板中的 el-* 组件由 unplugin-vue-components 按需引入（JS + 样式）
const app = createApp(App)
app.use(createPinia())
app.use(router)
app.directive('loading', ElLoading.directive)
app.mount('#app')
