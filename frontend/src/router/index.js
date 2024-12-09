import App from '../App.vue';
import { createRouter, createWebHistory } from 'vue-router';
import NotFound from './components/NotFound.vue'; //追記

const routes = [
  {
    path: '/', // ルートパスに設定
    name: 'TimeLeaf',
    code: 'code',
    component: App,
    meta: { title: 'TimeLeaf' }
  },
  {
    path: '/:pathMatch(.*)*', //ここから3行追記
    name: 'NotFound',
    component: NotFound
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;