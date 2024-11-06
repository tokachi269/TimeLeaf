import App from '../App.vue';
import { createRouter, createWebHistory } from 'vue-router';

const routes = [
    {
      path: '/', // ルートパスに設定
      name: 'code',
      component: App,
    },
  ];
  
  const router = createRouter({
    history: createWebHistory(process.env.BASE_URL),
    routes,
  });
  
  export default router;