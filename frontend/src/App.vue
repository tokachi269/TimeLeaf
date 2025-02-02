<template>
  <div id="app">
    <img alt="Vue logo" src="./assets/logo.png" class="logo" />
    <Header v-if="team != ''" :msg="headerMessage" />
    <TimelineView v-if="!invalidToken" :accessToken="accessToken" :accessedId="id" :accessedName="name" />
    <br>
    <br>
    <!-- フォロー中のチャンネルがない場合のメッセージ -->
    <div v-if="errorMessage" class="error-message"  v-html="errorMessage"></div>
  </div>
</template>

<script>
import Header from './components/Header.vue'
import TimelineView from './views/TimelineView.vue'
import { API_BASE_URL, API_REDIRECT_URL } from '@/config.js';
import { useRouter, useRoute } from 'vue-router';
import { ref, onMounted, watch } from 'vue';

export default {
  name: 'App',
  components: {
    Header,
    TimelineView,
  },
  data() {
    return {
      accessToken: null,
      invalidToken: true,
      team: "",
      errorMessage: "",
      id: "",
      name: "",
      scope: "",
    }
  },
  setup(props, { emit }) {
    const router = useRouter();
    const route = useRoute();
    const code = ref(null);
    // クエリパラメータを取得
    onMounted(async () => {
      // ルーターの初期化完了を待つ
      // これがないとパスパラが取れない
      await router.isReady();
      // クエリパラメータを取得
      code.value = route.query.code || '';
    });
    // codeが変更されたらinitを呼び出す
    watch(code, () => {
      //setup内はmethodを呼び出せないため文字列で呼び出す
      emit('init');

    });
    return {
      code,
    };
  },
  computed: {
    headerMessage() {
      return ` In ${this.team}.`;
    }
  },
  watch: {
    // codeが取得できるまで待機
    code() {
      this.init();
    },
  },
  methods: {
    async init() {
      //console.log('Code received in TimelineView:', this.code);
      //console.log('AccessToken received in TimelineView:', this.accessToken);
      // アプリ起動時にCookieをチェック
      this.accessToken = this.getCookie('token');
      this.id = this.getCookie('id');
      this.name = this.getCookie('name');
      this.scope = this.getCookie('scope');
      await this.fetchAccessToken();
    },
    async fetchAccessToken() {
      console.log("fetchAccessToken called")
      if (!this.accessToken && this.code == "") {
        //tokenもcodeもなければリダイレクト
        this.redirect();
        return;
      }
      const code = this.code;
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/getAccessToken?code=${code}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...(this.accessToken ? { 'Authorization': `Bearer ${this.accessToken}` } : {})
          }
        })
        if (response.ok) {
          const data = await response.json();
          if (data) {
            console.log('accessToken:', data);
            if (data.token) {
              this.accessToken = data.token;
              this.team = data.team;
              // トークンを保存
              document.cookie = `token=${this.accessToken}; expires=${new Date().setMonth(new Date().getMonth() + 1)}; path=/; SameSite=None; Secure`;
              if (data.scope) {
                document.cookie = `scope=${data.scope}; expires=${new Date().setMonth(new Date().getMonth() + 1)}; path=/; SameSite=None; Secure`;
              }
              if (data.id) {
                this.id = data.id;
                this.name = data.name;
                document.cookie = `id=${data.id}; expires=${new Date().setMonth(new Date().getMonth() + 1)}; path=/; SameSite=None; Secure`;
                document.cookie = `name=${data.name}; expires=${new Date().setMonth(new Date().getMonth() + 1)}; path=/; SameSite=None; Secure`;
              }
              this.invalidToken = false;
              this.removeUrlParams(); // パスパラメーターを削除
            }
            return
          }
          else {
            console.error('レスポンスに access_token が含まれていません:', data);
          }
        } else if (response.status == 400) {
          //tokenが失行している場合cookieから削除してリダイレクト
          if (response.type != "cors") {
            document.cookie = `id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=None; Secure`;
            document.cookie = `token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=None; Secure`;
            document.cookie = `scope=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=None; Secure`;
            document.cookie = `name=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; SameSite=None; Secure`;
            this.redirect();
            return;
          }
        }
        console.error(`リクエストに失敗しました。ステータスコード: ${response.status}`);

      } catch (error) {
        console.error('エラーが発生しました:', error);
        this.invalidToken = true;
      }
      this.errorMessage = `認証中にエラーが発生しました...<br>
      しばらく経ってから再度アクセスしてください。`;
    },
    getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
    },
    redirect() {
      const baseUrl = "https://slack.com/oauth/v2/authorize";
      const clientId = "REMOVED";
      const redirectUri = API_REDIRECT_URL;

      // 今後 `scope` や `user_scope` を追加しやすくするために配列で管理
      const scope = [];
      const userScope = [
        "emoji:read",
        "search:read",
        "reactions:read",
        "channels:read",
        "users.profile:read",
        "files:read",
        "channels:history",
        "reactions:write",
        "chat:write"
      ];

      // 配列をカンマ区切りの文字列に変換
      const scopeParam = scope.join(",");
      const userScopeParam = userScope.join(",");

      // URL を動的に構築
      const fullUrl = `${baseUrl}?scope=${encodeURIComponent(scopeParam)}&user_scope=${encodeURIComponent(userScopeParam)}&redirect_uri=${encodeURIComponent(redirectUri)}&client_id=${clientId}`;
      window.location.href = fullUrl;
    },
    removeUrlParams() {
      const url = new URL(window.location.href);
      url.search = ''; // クエリパラメーターを削除
      window.history.replaceState({}, document.title, url.toString());
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif, Georgia;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 10px;

}

.logo {
  /* 幅を200pxに設定 */
  width: 350px;
  /* 高さは自動で調整 */
  height: auto;
}

html {
  overflow-y: scroll;
}

img {
  user-select: none;
}
</style>