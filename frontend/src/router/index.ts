import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('../views/HomeView.vue') },
    { path: '/techs', name: 'techs', component: () => import('../views/TechsView.vue') },
    { path: '/diff', name: 'diff', component: () => import('../views/DiffView.vue') },
    { path: '/patch', name: 'patch', component: () => import('../views/PatchView.vue') },
    { path: '/version', name: 'version', component: () => import('../views/VersionView.vue') },
    { path: '/settings', name: 'settings', component: () => import('../views/SettingsView.vue') }
  ]
})

export default router
