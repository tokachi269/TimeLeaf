import App from '../App.vue';
import { createRouter, createWebHashHistory } from 'vue-router';
import NotFound from './components/NotFound.vue' //追記

const routes = [
  {
    path: '/', // ルートパスに設定
    name: 'TimeLeaf',
    code: 'code',
    component: App,
    meta: { title: 'TimeLeaf' }

  }, {
    path: '*', //ここから3行追記
    name: 'NotFound',
    component: NotFound
  },
];

const router = createRouter({
  mode: "history",
  history: createWebHashHistory("/"),
  routes,
});

export default router;