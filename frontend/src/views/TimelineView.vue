<template>
  <div class="timeline">
    <TimelineCard v-for="post in posts" :key="post.id" :post="post" />
    <div ref="infiniteScrollTrigger" class="loading-trigger">Loading...</div>
  </div>
</template>

<script>
import TimelineCard from '@/components/TimelineCard.vue';
import unicodeEmojis from '@/assets/emoji.json'; //https://raw.githubusercontent.com/iamcal/emoji-data/master/emoji.json

export default {
  components: { TimelineCard },
  props: {
    code: {
      type: String,
      required: true // 必須のプロパティとして設定
    }
  },
  data() {
    return {
      //accessToken: null,
      accessToken: 'xoxe.xoxp-1-Mi0yLTE4NTQ5MzMwMjI5Mi04NjQ3NzMyMzA0NzAtNzk4OTQyMTYzMjExMy04MDAwMjYyNTk4NDk3LWU1ODE1MjNlYTU5NTY3OTg0NDczOGI4ZDIxZDU5MTNhOTNiOGJkYzI0MDA0ZWI0YTBiYzIyMTMyZDhiMTQyYTI',
      posts: [], // タイムラインデータを保持
      page: 1, // ページ番号
      loading: false,
      next_cursor: null
    }
  },
  watch: {
    // codeが取得できるまで待機
    code(newCode) {
      if (newCode) {
        console.log('Code received in TimelineView:', this.code); // ここで確認
        this.loadPosts() // 初回データ読み込み
        this.initIntersectionObserver()
      }
    }
  },
  methods: {
    // APIまたはデータソースからの投稿を読み込む
    async loadPosts() {
      this.loading = true
      console.log('Slack Code in loadPosts:', this.code); // ここで確認
      if (this.accessToken == null) {
        this.accessToken = await fetch(`http://127.0.0.1:5000/api/v1/getAccessToken?code=${this.code}`, {
          method: 'GET', // HTTPメソッド
          headers: {
            'Content-Type': 'application/json' // コンテンツタイプをJSONに設定
          },
        }).then(response => {
          if (response.status != 200) {
            throw new Error('Network response was not ok'); // レスポンスがエラーの場合
          }
          return response.json(); // JSONとしてレスポンスをパース
        })
          .then(d => {
            // dataにはパースされたJSONが格納される
            console.log('accessToken:', d);

            // 特定のプロパティを取得
            return d; // ここで特定の値を取得
          })
          .catch(error => {
            console.error('Error fetching data:', error); // エラー処理
          });

      }
      // FlaskサーバーからSlackメッセージを取得
      const emojis = await fetch(`http://127.0.0.1:5000/api/v1/slack/emojis`, {
        method: 'GET', // HTTPメソッド
        headers: {
          'Authorization': `Bearer ${this.accessToken}` // コンテンツタイプをJSONに設定
        }
      }).then(response => {
        if (response.status != 200) {
          throw new Error('Network response was not ok'); // レスポンスがエラーの場合
        }
        return response.json(); // JSONとしてレスポンスをパース
      }).catch(error => {
        console.error('Error fetching data:', error); // エラー処理
      });
      console.log("emojiMap:", emojis);

      try {
        // FlaskサーバーからSlackメッセージを取得
        const response = await fetch(`http://127.0.0.1:5000/api/v1/slack/messages`, {
          method: 'POST', // HTTPメソッド
          headers: {
            'Content-Type': 'application/json', // コンテンツタイプをJSONに設定
            'Authorization': `Bearer ${this.accessToken}` // コンテンツタイプをJSONに設定
          },
          body: JSON.stringify({ token: this.accessToken, cursor: this.nextCursor == null ? '*' : this.nextCursor })
        })

        if (response.status == 200) {
          const data = await response.json()

          // Slackメッセージをタイムライン用にフォーマット
          const newPosts = data.matches.map((msg, i) => {
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
            return '&#x'+ unicodeEmoji.unified;  // Unicode絵文字を返す
          }

          return match;  // 見つからなければ元の文字列を返す
        });

        return {
          id: (this.page - 1) * 20 + i + 1,
          channelName: msg.channel.name,
          content: formattedContent,  // メッセージ内容 (画像に変換済み)
          attachments: msg.attachments,
          date: new Date(msg.ts * 1000).toLocaleDateString() // タイムスタンプを日付に変換
        };
      });

          this.nextCursor = data.pagination.next_cursor;
          this.posts.push(...newPosts);
          this.page++;
        } else {
          console.error("Failed to fetch messages:", response.error)
        }
      } catch (error) {
        console.error("Error fetching Slack messages:", error)
      } finally {
        this.loading = false
      }
    },
    // インフィニットスクロールの設定
    initIntersectionObserver() {
      const options = { root: null, rootMargin: '0px', threshold: 1.0 }
      this.observer = new IntersectionObserver(entries => {
        if (entries[0].isIntersecting && !this.loading) {
          this.loadPosts()
        }
      }, options)
      this.observer.observe(this.$refs.infiniteScrollTrigger)
    }
  },
  beforeUnmount() {
    if (this.observer) this.observer.disconnect()
  }
}
</script>

<style scoped>
.timeline {
  max-width: 600px;
  margin: auto;
  padding: 20px;
}

.loading-trigger {
  text-align: center;
  padding: 20px;
  font-weight: bold;
}
</style>