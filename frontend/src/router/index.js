import App from '../App.vue';
import { createRouter, createWebHashHistory } from 'vue-router';

const routes = [
    {
      path: '/', // ルートパスに設定
      name: 'TimeLeaf',
      code: 'code',
      component: App,
      meta: { title: 'TimeLeaf' }
    },
  ];
  
  const router = createRouter({
    history: createWebHashHistory("/"),
    routes,
  });
  
  export default router;