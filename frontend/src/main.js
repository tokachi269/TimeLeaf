import { createApp } from 'vue';
import App from './App.vue';
import router from './router/index.js'; // ルーターをインポート

// Vueアプリケーションを作成
const app = createApp(App);

// ルーターを登録
app.use(router);

// アプリケーションをマウント
app.mount('#app');