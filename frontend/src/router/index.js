import App from '../App.vue';
import { createRouter, createWebHashHistory } from 'vue-router';

const routes = [
    {
      path: '/', // ルートパスに設定
      code: 'code',
      component: App,
    },
  ];
  
  const router = createRouter({
    history: createWebHashHistory(),
    routes,
  });
  
  export default router;