import App from '../App.vue';
import { createRouter, createWebHistory } from 'vue-router';

const routes = [
    {
      path: '/', // ルートパスに設定
      code: 'code',
      component: App,
    },
  ];
  
  const router = createRouter({
    history: createWebHistory(),
    routes,
  });
  
  export default router;