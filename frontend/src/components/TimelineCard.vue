<template>
  <div class="card">
    <div class="channel-name">{{ post.channelName }}</div> <!-- チャンネル名を追加 -->
    <div class="header">
      <img :src="post.userImage" alt="User Image" class="user-image" />
      <div class="user-info">
        <span class="username">{{ post.username }}</span>
      </div>
    </div>
    <div class="content-wrapper">
      <div class="empty-space"></div>
      <div class="content-area">
        <div class="content" v-html="formattedContent"></div>
        <div v-if="thumbnailHtml" class="url-preview-container" v-html="thumbnailHtml"></div> <!-- サムネイル表示 -->
        <span class="date">{{ post.date }}</span>
      </div>
    </div>
  </div>
  <div class="reaction-container">
    <img v-for="reaction in post.reactions" :key="reaction.name" :src="getEmojiUrl(reaction.name)" :alt="reaction.name"
      class="reaction-image" />
  </div>
</template>

<script>
export default {
  props: {
    post: Object
  },
  data() {
    return {
      thumbnailHtml: '',
    };
  },
  computed: {
    formattedContent() {
      // テキスト内のURLを見つけ、サムネイルとタイトルを取得
      const urlRegex = /<(https?:\/\/[^\s]+)>/g;  // URL検出用の正規表現

      let formatted = this.post.content.replace(/\n/g, '<br>');

      formatted = formatted.replace(urlRegex, (match, url) => {
        return `<a href="http${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
      });
      return formatted;
    }
  },
  methods: {
    getEmojiUrl(emojiName) {
      // 絵文字名をURL形式に変換
      return `https://slack.com/img/emoji/${emojiName}.png`;
    },
    extractThumbnail() {
      if (this.post.attachments && this.post.attachments.length > 0) {
        const attachment = this.post.attachments[0]; // 最初の添付情報を取得
        if (attachment.image_url && attachment.title && attachment.title_link) {
          // サムネイル用HTMLを作成
          this.thumbnailHtml = `
            <div class="url-preview">
              <img src="${attachment.image_url}" alt="Thumbnail" class="url-thumbnail" />
              <div class="url-title">
                <a href="${attachment.title_link}" target="_blank">${attachment.title}</a>
              </div>
            </div>
          `;
        }
      }
    }
  },
  mounted() {
    this.extractThumbnail(); // コンポーネントがマウントされたときにサムネイル情報を抽出
  }
}
</script>

<style scoped>
/* cssの共通値 */
:root {
  --user-image-size: 50px;
  /* ユーザー画像のサイズ */
  --padding: 16px;
  /* パディング */
  --border-radius: 8px;
  /* ボーダーの角の丸み */
  --box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.1);
  /* ボックスシャドウ */
}

.card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  font-size: 16px;
  /* カード全体の基本フォントサイズ */
}

::v-deep .emoji-image {
  /* v-deepをつけないとv-htmlで挿入したhtmlタグにcssが適用されない */
  vertical-align: middle;
  /* テキストと画像の縦位置を合わせる */
  width: 1.1em;
  height: 1.1em;
  object-fit: contain;
  /* 画像の歪みを防ぐ */
}

::v-deep .emoji-image:hover {
  transform: scale(1.5);
  /* 画像を1.5倍に拡大 */
  animation: enlarge 0.1s ease forwards;
  /* enlargeアニメーションを適用 */
  z-index: 10;
  /* 他の要素よりも前に表示 */
}

/* アニメーションの定義 */
@keyframes enlarge {
  0% {
    transform: scale(1);
    /* 通常のサイズ */
  }

  100% {
    transform: scale(1.5);
    /* 1.5倍に拡大 */
  }
}

.channel-name {
  font-weight: bold;
  margin-bottom: 8px;
  /* ユーザー情報との間にマージンを追加 */
}

.header {
  display: flex;
  align-items: flex-start;
  /* 画像とユーザー情報を上に揃える */
}

.user-image {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 10px;
}

.user-info {
  flex-grow: 1;
  /* ユーザー情報が残りのスペースを占める */
}

.username {
  font-size: 0.9em;
  color: #333;
}

.content-wrapper {
  display: flex;
  margin-top: 10px;
  align-items: flex-start;
}

.empty-space {
  width: 40px;
  flex-shrink: 0;
}

.content-area {
  flex-grow: 1;
  /* 残りのスペースを使用 */
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  margin-right: 20px;
  /* 空白を追加して余白を調整 */
}

.content {
  margin-bottom: 5px;
  text-align: left;
}

::v-deep a {
  word-wrap: break-word;      /* 長いURLを折り返す */
  overflow-wrap: break-word;  /* URLを強制的に折り返す */
  white-space: normal;        /* 改行を許可 */
}

.date {
  color: #aaa;
  font-size: 0.9em;
  text-align: right;
}

::v-deep .url-preview {
  display: flex;
  align-items: center;
  margin-top: 10px;
}

::v-deep .url-thumbnail {
  max-width: 100px;
  margin-right: 10px;
  border-radius: 8px;
}

::v-deep  .url-title {
  font-size: 14px;
}

::v-deep .url-title a {
  color: #1a73e8;
  text-decoration: none;
}

::v-deep .url-title a:hover {
  text-decoration: underline;
}

::v-deep .url-preview-container {
  margin-top: 20px;
}
</style>