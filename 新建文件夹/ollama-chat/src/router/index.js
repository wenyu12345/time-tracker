import { createRouter, createWebHashHistory } from 'vue-router'
import ChatLayout from '../layouts/ChatLayout.vue'

const routes = [
  {
    path: '/',
    component: ChatLayout,
    children: [
      {
        path: '',
        name: 'chat',
        component: () => import('../views/ChatView.vue')
      },
      {
        path: '/models',
        name: 'models',
        component: () => import('../views/ModelsView.vue')
      },
      {
        path: '/settings',
        name: 'settings',
        component: () => import('../views/SettingsView.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router