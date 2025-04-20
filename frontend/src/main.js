import { createApp } from 'vue';
import App from './App.vue';
import router from './router/index.js';
import './config.js';

const app = createApp(App);

app.use(router);

app.mount('#app');