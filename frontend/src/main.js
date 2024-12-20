import { createApp } from 'vue';
import App from './App.vue';
import router from './router/index.js'; // ルーターをインポート
import { VPullToRefresh } from 'vuetify/labs/VPullToRefresh';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';
import { createVuetify } from 'vuetify';

// Vueアプリケーションを作成
const app = createApp(App);
const vuetify = createVuetify({
    components: {
      ...components,
      VPullToRefresh
    },
    directives,
  });
  
 app.use(vuetify);
// ルーターを登録
app.use(router);

// アプリケーションをマウント
app.mount('#app');