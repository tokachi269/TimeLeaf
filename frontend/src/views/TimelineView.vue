<template>
  <div class="timeline">
    <!-- タイムライン切り替えボタン -->
    <div class="timeline-toggle">
      <button :class="{ 'active': !isFollowing }" @click="toggleTimeline(false)">全体</button>
      <button :class="{ 'active': isFollowing }" @click="toggleTimeline(true)">フォロー中</button>
    </div>

    <!-- タイムラインカードの表示 -->
    <TimelineCard v-for="post in posts" :key="post.id" :post="post" :accessToken="accessToken" :emojiMap="emojiMap" />
    <!-- フォロー中のチャンネルがない場合のメッセージ -->
    <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>

    <!-- 無限スクロールのトリガー -->
    <div ref="infiniteScrollTrigger" class="loading-trigger">
      <div v-if="loading">ロード中...</div>
    </div>
  </div>
</template>

<script>
import TimelineCard from '@/components/TimelineCard.vue';
import unicodeEmojis from '@/assets/emoji.json'; //https://raw.githubusercontent.com/iamcal/emoji-data/master/emoji.json
import { API_BASE_URL } from '@/config.js';

export default {
  components: { TimelineCard },
  props: {
    accessToken: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      isFollowing: true, // フォロー中タイムラインor全体タイムラインを管理
      posts: [], // タイムラインデータを保持
      page: 1, // ページ番号
      loading: false,
      nextCursor: null,
      emojiMap: [],
      errorMessage: '', // エラーメッセージを格納する変数
    }
  },
  provide() {
    return {
      unicodeEmojis: unicodeEmojis,
    };
  },
  computed: {
    computedEmojiMap() {
      return this.emojiMap || [];
    },
  },
  async mounted() {
    this.init();
  },
  methods: {
    async init() {
      console.log("TimelineCard called");
      this.isFollowing = "true" === this.getCookie('isFollowing').toLowerCase() ;
      this.fetchPosts();
    },
    fetchPosts() {
      if (this.accessToken) {
        this.resetPosts();
        this.initIntersectionObserver();
      }
      this.loading = false
    },
    toggleTimeline(isFollowing) {
      // ローディング中でないかつ現在の状態と異なる場合、タイムラインを更新
      if (!this.loading) {
        if (this.isFollowing !== isFollowing) {
          this.isFollowing = isFollowing;
          this.nextCursor = null;
          this.errorMessage = "";
          this.fetchPosts();
          document.cookie = `isFollowing=${this.isFollowing}; expires=${new Date().setMonth(new Date().getMonth() + 1)}; path=/; SameSite=None; Secure`;
        }
      }
    },
    resetPosts() {
      // 投稿データと表示をリセット
      this.posts = [];
      this.$nextTick(() => {
        // 投稿をリセット後に表示済みのカードを削除
        const timelineCards = this.$el.querySelectorAll('TimelineCard');
        timelineCards.forEach(card => card.remove());
      });
    },
    makeQuery(channels) {
      // チャンネル名だけを抽出して、in: 形式で文字列にする
      const channelNames = channels.map(channel => channel.name);
      return 'in:' + channelNames.join(' in:');  // 'in:'で区切って結合
    },
    async loadPosts() {
      // APIまたはデータソースからの投稿を読み込む
      console.log("loadPosts called");

      this.loading = true;

      // FlaskサーバーからSlackメッセージを取得
      const channels = await fetch(`${API_BASE_URL}/api/v1/slack/timesChannels`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${this.accessToken}`
        }
      }).then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      }).catch(error => {
        console.error('Error fetching data:', error);
      });
      console.log("channelMap:", channels);

      // FlaskサーバーからSlacke絵文字を取得
      const emojis = await fetch(`${API_BASE_URL}/api/v1/slack/emojis`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${this.accessToken}`
        }
      }).then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      }).catch(error => {
        console.error('Error fetching data:', error);
      });
      this.emojiMap = emojis;
      console.log("emojiMap:", this.emojiMap);
      // フォロー中のチャンネルがない場合
      if (this.isFollowing && channels.followed_channels.length === 0) {
        this.errorMessage = 'フォローしているチャンネルがありません';
        this.loading = false
      } else {
        try {
          // FlaskサーバーからSlackメッセージを取得
          const response = await fetch(`${API_BASE_URL}/api/v1/slack/messages?cursor=${encodeURIComponent(this.nextCursor == null ? '*' : this.nextCursor)}&query=${(this.isFollowing ? encodeURIComponent(this.makeQuery(channels.followed_channels)) : encodeURIComponent(this.makeQuery(channels.channels)))}`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${this.accessToken}`
            }
          })

          if (response.status == 200) {
            const messages = await response.json();
            console.log("messageMap:", messages);

            // Slackメッセージをタイムライン用にフォーマット
            const newPosts = messages.matches.map((msg, i) => {
              // メッセージ内容に含まれる絵文字コードを画像URLまたはUnicodeに変換
              let formattedContent = msg.text.replace(/:([^\s:]+):/g, (match, emojiName) => {
                // emojiMap から画像URLを取得し、該当する画像タグに変換
                const emojiUrl = emojis[emojiName];
                if (emojiUrl) {
                  return `<img src="${emojiUrl}" alt="${emojiName}" class="emoji-image">`;
                }

                // emojiMapに存在しない場合、unicodeEmojisで検索
                const unicodeEmoji = unicodeEmojis.find(emoji => emoji.short_name === emojiName);
                if (unicodeEmoji) {
                  return `<span class="emoji-image">${this.convertToHtmlEntity(unicodeEmoji.unified)}</span>`;  // Unicode絵文字を返す
                }

                return match;  // 見つからなければ元の文字列を返す
              });

              // チャンネルの創設者と と メッセージのuserIDが一致するかをチェック
              const channel = channels.followed_channels.find(channel => channel.id === msg.channel.id);
              const isMaster = channel ? channel.creator === msg.user : false;

              // 正規表現でマッチ
              formattedContent = formattedContent.replace(/<@(\w+)\s*\|([^\\>]+)>/g, (_, id, name) => {
                return `<span class="mention" data-id="${id}">@${name}</span>`;
              });
              return {
                id: (this.page - 1) * 20 + i + 1,
                ts: msg.ts,
                userId: msg.user,
                userNeme: msg.username,
                channelId: msg.channel.id,
                channelName: "#" + msg.channel.name,
                channelUrl: msg.permalink,
                isMaster: isMaster,
                content: formattedContent,  // メッセージ内容 (画像に変換済み)
                attachments: msg.attachments,
                files: msg.files,
                date: new Date(msg.ts * 1000).toLocaleString(), // タイムスタンプを日付に変換
              };
            });
            this.nextCursor = messages.pagination.next_cursor;
            this.posts.push(...newPosts);
            this.page++;
            this.errorMessage = '';
          } else {
            console.error("Failed to fetch messages:", response.error)
          }
        } catch (error) {
          console.error("Error fetching Slack messages:", error)
          this.errorMessage = 'データの取得中にエラーが発生しました';
        } finally {
          this.loading = false
        }
      }
    },
    // インフィニットスクロールの設定
    initIntersectionObserver() {
      //スクロールしたら自動ロード
      //よくわからないけど動いてるからOK
      console.log("initIntersectionObserver called")
      const options = { root: null, rootMargin: '800px', threshold: 1.0 }
      this.observer = new IntersectionObserver(entries => {
        if (entries[0].isIntersecting && !this.loading) {
          this.loadPosts()
        }
      }, options)
      this.observer.observe(this.$refs.infiniteScrollTrigger)
    },
    convertToHtmlEntity(unicodeString) {
      // ハイフンで分割して、各部分に &#x と ; を追加
      // 絵文字の性別や肌の色が指定されている場合にこれが実行される
      return unicodeString
        .split('-')
        .map(code => `&#x${code};`)
        .join('');
    },
    getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
    },
  },
  beforeUnmount() {
    if (this.observer) this.observer.disconnect()
  }
}
</script>

<style scoped>
.timeline-toggle {
  user-select: none;
  display: flex;
  /* border-bottom: 2px solid #ccc; */
  margin-bottom: 20px;
}

.timeline-toggle button {
  flex: 1;
  padding: 10px;
  background-color: #f9f9f9;
  border: none;
  font-size: 1em;
  cursor: pointer;
  text-align: center;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.timeline-toggle button.active {
  background-color: #94ca68;
  color: white;
  font-weight: bold;
}

.timeline-toggle button:not(.active):hover {
  background-color: #e0e0e0;
}

.loading-trigger {
  text-align: center;
  font-size: 14px;
  color: #888;
}

.timeline {
  max-width: 600px;
  margin: auto;
  padding: 10px;
}

.loading-trigger {
  text-align: center;
  padding: 20px;
  font-weight: bold;
}
</style>