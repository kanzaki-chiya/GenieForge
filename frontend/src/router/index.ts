import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('../views/HomeView.vue') },
    { path: '/techs', name: 'techs', component: () => import('../views/TechsView.vue') },
    { path: '/units', name: 'units', component: () => import('../views/UnitsView.vue') },
    { path: '/civs', name: 'civs', component: () => import('../views/CivsView.vue') },
    { path: '/effects', name: 'effects', component: () => import('../views/EffectsView.vue') },
    { path: '/diff', name: 'diff', component: () => import('../views/DiffView.vue') },
    { path: '/patch', name: 'patch', component: () => import('../views/PatchView.vue') },
    { path: '/version', name: 'version', component: () => import('../views/VersionView.vue') },
    { path: '/settings', name: 'settings', component: () => import('../views/SettingsView.vue') }
  ]
})

export default router
