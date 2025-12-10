<template>
  <div id="app">
    <div class="header-blur-bar"></div>
    <img alt="Vue logo" src="./assets/logo.png" :class="['logo', { 'scrolled': isScrolled }]" :style="{ width: logoWidth + 'px', top: logoTop + 'px' }" @click="reloadPage" />
    <div class="header-container">
      <Header v-if="team != ''" :msg="headerMessage" />
      <!-- 設定モーダルを呼び出すボタン -->
      <img src="./assets/setting.png" alt="設定" class="settings-button invert-on-dark-mode" @click="openSettingsModal" />
    </div>
    <!-- 設定モーダル -->
    <SettingsModal :show="showSettingsModal" @close="closeSettingsModal" @toggle-darkMode="toggleSetting"
      @toggle-smallSwitch="toggleSetting" @open-changelog="openChangelogModal" />
    
    <!-- 更新履歴モーダル -->
    <ChangelogModal :is-visible="showChangelogModal" :is-new-version="isNewVersion" :changelog="changelog" :expanded-versions="expandedVersions"
      @close="closeChangelogModal" />

    <TimelineView v-if="!invalidToken" :accessToken="accessToken" :accessedId="id" :accessedName="name" />
    <br>
    <br>
    <!-- フォロー中のチャンネルがない場合のメッセージ -->
    <div v-if="errorMessage" class="error-message" v-html="errorMessage"></div>
  </div>
</template>

<script>
import Header from './components/Header.vue'
import TimelineView from './views/TimelineView.vue'
import SettingsModal from './components/SettingsModal.vue'
import ChangelogModal from './components/ChangelogModal.vue'
import { API_BASE_URL, API_REDIRECT_URL,SLACK_CLIENT_ID } from '@/config.js';
import { useRouter, useRoute } from 'vue-router';
import { ref, onMounted, watch } from 'vue';
import { saveVersionToCookie, saveUserIdToCookie, getUserIdFromCookie, getVersionFromCookie, isVersionUpdated } from '@/utils/cookieUtils.js';
import versionData from '@/assets/version.json';

export default {
  name: 'App',
  components: {
    Header,
    TimelineView,
    SettingsModal,
    ChangelogModal
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
      showSettingsModal: false,
      isDarkMode: false,
      // バージョン管理関連
      showChangelogModal: false,
      isNewVersion: false,
      changelog: [],
      currentVersion: versionData.version,
      versionChecked: false,
      expandedVersions: [],
      // スクロール状態
      isScrolled: false,
      logoWidth: 350,  // ロゴの現在の幅
      maxLogoWidth: 350,  // ロゴの最大幅
      minLogoWidth: 100,  // ロゴの最小幅
      logoTop: 10  // ロゴの上からの位置
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
  mounted() {
    // OSの設定を読み込む
    const savedTheme = localStorage.getItem('darkMode');
    if (savedTheme === null) {
      this.isDarkMode = false;//prefersDarkScheme;
    } else {
      this.isDarkMode = savedTheme === 'true';
    }
    this.applyTheme();
    
    // スクロールイベントリスナーを追加
    window.addEventListener('scroll', this.handleScroll);
  },
  beforeUnmount() {
    // スクロールイベントリスナーを削除
    window.removeEventListener('scroll', this.handleScroll);
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
              if (!this.versionChecked) {
                this.checkVersion();
                this.versionChecked = true;
              }
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
      const clientId = SLACK_CLIENT_ID;
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
    },
    openSettingsModal() {
      this.showSettingsModal = true;
    },
    closeSettingsModal() {
      this.showSettingsModal = false;
    },
    toggleSetting() {
      this.isDarkMode = !this.isDarkMode;
      this.applyTheme();
    },
    applyTheme() {
      if (this.isDarkMode) {
        console.log("applyTheme.body.classList.add('dark-mode');");

        document.body.classList.add('dark-mode');
      } else {
        document.body.classList.remove('dark-mode');
      }
    },
    /**
     * バージョンをチェックし、新バージョンなら更新履歴を表示
     */
    checkVersion() {
      // バージョン情報を読み込む
      this.changelog = versionData.changelog;
      
      // ユーザーIDをCookieに保存（初回アクセスの判定用）
      let userId = getUserIdFromCookie();
      if (!userId) {
        // 初回アクセス時はランダムなユーザーIDを生成
        userId = 'user_' + Math.random().toString(36).substr(2, 9);
        saveUserIdToCookie(userId);
      }
      const savedVersion = getVersionFromCookie();

      if (!savedVersion) {
        // トークンCookieが存在しない完全新規ユーザーは更新履歴を表示しない
        saveVersionToCookie(this.currentVersion);
        this.expandedVersions = [];
        return;
      }

      this.expandedVersions = this.computeExpandedVersions(savedVersion);
      
      // バージョンが更新されているかチェック
      if (isVersionUpdated(this.currentVersion)) {
        // 新バージョンの場合、更新履歴モーダルを表示
        this.isNewVersion = true;
        this.showChangelogModal = true;
        
        // バージョン情報をCookieに保存
        saveVersionToCookie(this.currentVersion);
      }
    },
    computeExpandedVersions(savedVersion) {
      if (!savedVersion) {
        return this.changelog.map((entry) => entry.version);
      }
      return this.changelog
        .filter((entry) => this.compareVersions(entry.version, savedVersion) > 0)
        .map((entry) => entry.version);
    },
    compareVersions(versionA, versionB) {
      const partsA = versionA.split('.').map((part) => parseInt(part, 10) || 0);
      const partsB = versionB.split('.').map((part) => parseInt(part, 10) || 0);
      const length = Math.max(partsA.length, partsB.length);
      for (let i = 0; i < length; i += 1) {
        const diff = (partsA[i] || 0) - (partsB[i] || 0);
        if (diff !== 0) {
          return diff > 0 ? 1 : -1;
        }
      }
      return 0;
    },
    /**
     * 更新履歴モーダルを開く（設定画面から呼び出される）
     */
    openChangelogModal() {
      this.isNewVersion = false; // 設定から開いた場合は新バージョン表示ではない
      this.showChangelogModal = true;
    },
    /**
     * 更新履歴モーダルを閉じる
     */
    closeChangelogModal() {
      this.showChangelogModal = false;
      this.isNewVersion = false;
    },
    /**
     * スクロールイベントハンドラー
     */
    handleScroll() {
      const scrollY = window.scrollY;
      
      // スクロール量に応じてロゴのサイズを計算
      // 1pxスクロールごとにロゴを1px縮小
      const newWidth = this.maxLogoWidth - scrollY;
      
      // 最小幅と最大幅の範囲内に収める
      if (newWidth >= this.minLogoWidth && newWidth <= this.maxLogoWidth) {
        this.logoWidth = newWidth;
        this.logoTop = 10;
      } else if (newWidth < this.minLogoWidth) {
        this.logoWidth = this.minLogoWidth;
        this.logoTop = 10; // 最小サイズ時も画面上部に固定
      } else {
        this.logoWidth = this.maxLogoWidth;
        this.logoTop = 10;
      }
      
      // 最小サイズに到達したら固定表示フラグを立てる
      this.isScrolled = this.logoWidth <= this.minLogoWidth;
    },
    /**
     * ページをリロードする
     */
    reloadPage() {
      window.location.reload();
    }
  }
}
</script>

<style>
:root {
  /* カラー */
  --background-body: #f9f9f9;
  --background-card-body: #ffffff;
  --background-card-border: #ddd;
  --text-base-color: #1e1e1e;
  --text-secound-color: #6e6e6e;
  --text-url-color: #1a73e8;
  --text-url-hover-color: #2064bc;
  --modal-background-color: #fefefe;
  --button-active-background-color: rgb(148, 202, 104);
  --button-active-text-color: white;
  --button-notactive-background-color: #ededed;
  --button-notactive-text-color: #1c1c1c;
  --button-notactive-hover-background-color: #e1e1e1;
  --hover-color: rgba(0, 0, 0, 0.05);
  --border-color: #ddd;
  --secondary-text-color: #6e6e6e;
  
  /* スペーシング */
  --spacing-xxs: 2px;
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 12px;
  --spacing-lg: 16px;
  --spacing-xl: 20px;
  --spacing-2xl: 24px;
  --spacing-3xl: 32px;
  
  /* ボーダー */
  --border-radius-sm: 6px;
  --border-radius-md: 8px;
  --border-radius-lg: 12px;
  --border-width: 1px;
  --border-width-md: 2px;
  
  /* シャドウ */
  --shadow-none: none;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 20px rgba(0, 0, 0, 0.15);
  --shadow-xl: 0 20px 40px rgba(0, 0, 0, 0.2);
  
  /* z-index */
  --z-base: 1;
  --z-header: 100;
  --z-modal: 1000;
  --z-modal-overlay: 10000;
  
  /* フォント */
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  
  /* トランジション */
  --transition-fast: 0.15s ease;
  --transition-normal: 0.2s ease;
  --transition-slow: 0.3s ease;
}

body.dark-mode {
  --background-body: #171717;
  --background-card-body: #191919;
  --background-card-border: #686868;
  --text-base-color: #b1b1b1;
  --text-secound-color: #7f7f7f;
  --text-url-color: #99bdec;
  --text-url-hover-color: #74a1dc;
  --modal-background-color: #2c2c2c;
  --button-active-background-color: rgb(125 169 88);
  --button-active-text-color: white;
  --button-notactive-background-color: #272727;
  --button-notactive-hover-background-color: #242424;
  --button-notactive-text-color: rgb(232, 232, 232);
  --hover-color: rgba(255, 255, 255, 0.05);
  --border-color: #686868;
  --secondary-text-color: #7f7f7f;
}

body {
  background-color: var(--background-body);
  color: var(--text-base-color);
}
img.invert-on-dark-mode {
  transition: filter 0.3s ease;
}

body.dark-mode img.invert-on-dark-mode {
  filter: invert(1);
}
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif, Georgia;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: var(--text-base-color);
  padding-top: 50px;
  background-color: var(--background-body);
}

/* ヘッダーのぼかしバー */
.header-blur-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 80px;
  -webkit-mask-image: linear-gradient(to bottom, black 0%, black 60%, transparent 100%);
  mask-image: linear-gradient(to bottom, black 0%, black 60%, transparent 100%);
  backdrop-filter: blur(4px) saturate(180%);
  -webkit-backdrop-filter: blur(4px) saturate(180%);
  z-index: var(--z-header);
  pointer-events: none;
}

.logo {
  height: auto;
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  cursor: pointer;
  transition: none;
  z-index: calc(var(--z-header) + 1);
}

img.logo {
  transition: filter var(--transition-slow);
}

body.dark-mode img.logo {
  filter: brightness(0.9) saturate(1.1);
}

.header-container {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0 auto;
  max-width: 600px;
  width: 100%;
  padding: 0 20px;
  height: 50px;
  position: relative;
}

.header-container Header {
  flex: 1;
  text-align: center;
}
@media (max-width: 600px) {
  .header-container {
    max-width: 100%;
    padding: 0 0px;
  }
}
.settings-button {
  position: absolute;
  right: 20px;
  z-index: 1000;
  cursor: pointer;
  width: 20px;
  height: 20px;
}

html {
  overflow-y: scroll;
}

img {
  user-select: none;
}
</style>