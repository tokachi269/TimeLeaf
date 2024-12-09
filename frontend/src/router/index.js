import App from '../App.vue';
import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/', // ルートパスに設定
    name: 'TimeLeaf',
    code: 'code',
    component: App,
    meta: { title: 'TimeLeaf' }
  }
];

const router = createRouter({
  history: createWebHistory("/"),
  routes,
});

export default router;