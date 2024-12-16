<template>
  <div class="timeline">
    <!-- タイムライン切り替えボタン -->
    <div class="timeline-toggle">
      <button :class="{ 'active': !isFollowing }" @click="toggleTimeline(false)">全体</button>
      <button :class="{ 'active': isFollowing }" @click="toggleTimeline(true)">フォロー中</button>
    </div>

    <!-- 絵文字ピッカー -->
    <div v-if="showEmojiPicker" :style="{ top: pickerPosition.top + 'px', left: pickerPosition.left + 'px' }"
      class="emoji-picker modal">
      <Picker :data="emojiIndex" set="google" title="サーバー絵文字は現在未実装です" @select="selectReaction" />
    </div>
    <!-- タイムラインカード -->
    <TimelineCard v-for="post in posts" :key="post.id" :post="post" :accessToken="accessToken" :emojiMap="emojiMap"
      @open-picker="handleOpenPicker" @add-reaction="handleOpenPicker" ref="timelineCards" />
    <!-- フォロー中のチャンネルがない場合のメッセージ -->
    <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>

    <!-- 無限スクロールのトリガー -->
    <div ref="infiniteScrollTrigger" class="loading-trigger">
      <div v-if="loading">Loading...</div>
    </div>
  </div>
</template>

<script>
import TimelineCard from '@/components/TimelineCard.vue';
import unicodeEmojis from '@/assets/emoji.json'; //https://raw.githubusercontent.com/iamcal/emoji-data/master/emoji.json
import { API_BASE_URL } from '@/config.js';
import "emoji-mart-vue-fast/css/emoji-mart.css";
import { Picker, EmojiIndex } from "emoji-mart-vue-fast/src";
import data from "emoji-mart-vue-fast/data/google.json";

export default {
  components: { TimelineCard, Picker },
  props: {
    accessToken: {
      type: String,
      required: true
    },
    accessedName: {
      type: String,
      required: true
    },
    accessedId: {
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
      showEmojiPicker: false,
      selectedPostId: null,
      emojiIndex: null,
      pickerPosition: {
        top: 0, // Pickerの高さを考慮して調整
        left: 0
      }, // Pickerのスタイルを格納する変数
      isScrolling: false,
      isTapped: false, // タップ状態を管理
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
  watch: {
    showEmojiPicker(newVal) {
      if (newVal) {
        setTimeout(() => {
          window.addEventListener("touchstart", this.closeEmojiPickerOnTapOrClick);
          window.addEventListener("click", this.closeEmojiPickerOnTapOrClick);
        }, 0);
      } else {
        window.removeEventListener("touchstart", this.closeEmojiPickerOnTapOrClick);
        window.removeEventListener("click", this.closeEmojiPickerOnTapOrClick);
      }
    }
  },
  async mounted() {
    this.init();
    window.addEventListener("resize", this.checkHeight); // imageGalleryのサイズ変更(画像が呼び込まれた)検知
    window.addEventListener("scroll", this.onScroll); // スクロール検知
    // タップイベントリスナー (スマホ)
  },
  beforeUnmount() {
    window.removeEventListener("resize", this.checkHeight);
    window.removeEventListener("scroll", this.onScroll);

    // タップイベントリスナー (スマホ)
    window.removeEventListener("touchstart", this.closeEmojiPickerOnTapOrClick);
    window.removeEventListener("click", this.closeEmojiPickerOnTapOrClick);

    if (this.observer) this.observer.disconnect()
  },
  methods: {
    async init() {
      console.log("TimelineCard called");
      this.isFollowing = this.getCookie('isFollowing')?.toLowerCase() === "true";
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
      const emojis = await fetch(`${API_BASE_URL}/api/v2/slack/emojis`, {
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
      this.emojiIndex = new EmojiIndex(data, { custom: emojis })
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
                const emoji = this.emojiMap.find(e => e.name === emojiName);
                if (emoji) {
                  return `<img src="${emoji.imageUrl}" alt="${emoji.name}" class="emoji-image">`;
                }

                // emojiMapに存在しない場合、unicodeEmojisで検索
                const unicodeEmoji = unicodeEmojis.find(emoji => emoji?.short_name === emojiName);
                if (unicodeEmoji) {
                  return `<span class="emoji-image">${this.convertToHtmlEntity(unicodeEmoji.unified)}</span>`;  // Unicode絵文字を返す
                }

                return match;  // 見つからなければ元の文字列を返す
              });

              // チャンネルの創設者と と メッセージのuserIDが一致するかをチェック
              const channel = channels.followed_channels.find(channel => channel.id === msg.channel.id);
              const isMaster = channel ? channel.creator === msg.user : false;
              formattedContent = formattedContent.replace(/\n/g, '<br>');

              // 正規表現でマッチ
              formattedContent = this.replaceHtmlTag(formattedContent.replace(/<@(\w+)\s*\|([^\\>]+)>/g, (_, id, name) => {
                return `<span class="mention" data-id="${id}">@${name}</span>`;
              }));
              return {
                accessedName: this.accessedName,
                accessedId: this.accessedId,
                id: (this.page - 1) * 20 + i + 1,
                ts: msg.ts,
                userId: msg.user,
                userNeme: msg.username,
                channelId: msg.channel.id,
                channelName: "#" + msg.channel.name,
                channelUrl: msg.permalink,
                isMaster: isMaster,
                content: formattedContent,  // メッセージ内容 (画像に変換済み)
                thumbnailHtmls: msg.attachments,
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
    replaceHtmlTag(content) {
      // 正規表現: URL単体またはラベル付きURLにマッチ
      const pattern = /<(https?:\/\/[^|>]+)\|([^>]+)>|<(https?:\/\/[^>]+)>/g;

      // コールバック関数で置換処理
      return content.replace(pattern, (match, url1, label1, url2) => {
        // URLとラベルを選択
        const url = url1 || url2; // URLをキャプチャ
        const label = label1 || url; // ラベルがなければURLをそのまま使用

        // URLまたはラベルが取得できなければ元の文字列を返す
        if (!url) {
          return match; // マッチした元の文字列をそのまま返す
        }

        return `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`;
      });
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
    onScroll() {
      // ユーザーポップアップが表示されている場合は閉じる
      this.isScrolling = true;
      if (this.showEmojiPicker) {
        this.showEmojiPicker = false;
      }
      // 100ms 後にスクロールが止まったと判断
      clearTimeout(this.scrollTimeout);
      this.scrollTimeout = setTimeout(() => {
        this.isScrolling = false;
      }, 100);
    },
    closeEmojiPickerOnTapOrClick(event) {
      console.log("closeEmojiPickerOnTapOrClick called");

      // 絵文字ピッカーが表示されている場合にタップまたはクリックを検知して閉じる
      if (this.showEmojiPicker) {
        const pickerElement = this.$el.querySelector('.emoji-picker');
        if (pickerElement && !pickerElement.contains(event.target)) {
          this.showEmojiPicker = false;
        }
      }
    },
    selectReaction(emoji) {
      this.emojisOutput = this.emojisOutput + emoji.native;
      this.showEmojiPicker = false;
      console.log(this.selectedPostId);
      // カードのコンポーネントを取得して絵文字を送信
      const card = this.$refs.timelineCards.find(card => card.localPost.ts === this.selectedPostId);
      card.handleEmojiSelected(emoji);
    },
    handleOpenPicker(ts, event) {
      this.selectedPostId = ts;
      this.showEmojiPicker = true;
      // ホバーした要素の位置を取得
      const targetElement = event.currentTarget;
      const rect = targetElement.getBoundingClientRect();

      // Pickerの位置を設定
      this.pickerPosition = {
        top: rect.bottom + window.scrollY + 10, // スクロール量を考慮
      };

      // 画面からはみ出ないように調整
      const pickerHeight = 420; // 絵文字ピッカーの高さ
      const pickerWidth = 355; // 絵文字ピッカーの幅
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      if (this.pickerPosition.left + pickerWidth > viewportWidth) {
        this.pickerPosition.left = viewportWidth - pickerWidth - 10;
      }
      if (this.pickerPosition.top + pickerHeight > viewportHeight) {
        this.pickerPosition.top = viewportHeight - pickerHeight - 10;
      }
    },
  },
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
  background-color: rgb(148, 202, 104);
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

.emoji-picker {
  position: absolute;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: center;
  /* 中央揃え */
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  z-index: 9999;
}
</style>