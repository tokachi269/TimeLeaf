<template>
  <div class="card">
    <a :href="localPost.channelUrl" class="channel-name" target="_blank" rel="noopener noreferrer"> {{
      localPost.channelName }} </a>
    <div class="header">
      <img :src="userImage" alt="User Image" class="user-image" />
      <div class="user-info">
        <span class="username">{{ userName }}</span>
        <span class="username-en">{{ userNameEn }}</span>
      </div>
    </div>
    <div class="content-wrapper">
      <div class="empty-space"></div>
      <div class="content-area">
        <div class="content" v-html="localPost.content"></div>
        <div v-if="thumbnailHtml" class="url-preview-container" v-html="thumbnailHtml"></div> <!-- サムネイル表示 -->
        <div v-if="hasImage">
          <div ref="imageGallery" class="image-gallery" :class="[setGalleryClass, { 'expanded': isExpanded }]">
            <div v-for="(file, index) in visibleImages" :key="index" class="image-item">
              <img :src="file.url" :alt="file.name" class="image" @click="openModal(index)" crossorigin="anonymous" />
            </div>
            <div v-if="isModalOpen" class="modal" @click="closeModal">
              <img :src="modalImageUrl" alt="High Quality Image" class="modal-image" crossorigin="anonymous" />
            </div>
          </div>
          <button v-if="shouldShowExpandButton" class="expand-button" @click="toggleExpanded">
            <span class="expand-button-context">もっと見る</span>
          </button>
        </div>
        <div class="reaction-list">
          <div v-for="reaction in reactions" :key="reaction.name" class="reaction-item"
            :class="{ 'highlight': checkHighlight(reaction) }" @mouseenter="showUserList(reaction.name, $event)"
            @mouseleave="hideUserList" @click="insertOrDeleteReaction(reaction.name, true)"
            @mousedown="handleReactionMouseDown(reaction.name, $event)" @mouseup="handleReactionMouseUp"
            @touchstart="handleReactionMouseDown(reaction.name, $event)" @touchend="handleReactionMouseUp">
            <span v-html="getEmojiForReaction(reaction.name)"></span>
            <span class="reaction-count">{{ reaction.count }}</span>
          </div>
          <div v-if="reactions.length != 0" @click="openEmojiPicker($event)" class="reaction-item"> <img
              src="./../assets/emoji-add.png" alt="Add Reaction" class="emoji-image">
          </div>

          <!-- ユーザーポップアップ -->
          <div v-if="isUserListVisible" class="user-popup"
            :class="{ 'is-scrolling': isScrolling, 'is-tapped': isTapped }"
            :style="{ top: popupPosition.top + 'px', left: popupPosition.left + 'px' }">
            <!-- リアクション名を表示 -->
            <div class="reaction-name">:{{ hoveredReactionName }}:</div>
            <hr class="separator-line" />
            <ul>
              <li v-for="user in hoveredUsers" :key="user">{{ user }}</li>
            </ul>
          </div>
        </div>
        <div class="detail-list">
          <div v-if="reactions.length == 0" @click="openEmojiPicker($event)" class="add-reaction-image">
            <img src="./../assets/emoji-add.png" alt="Add Reaction" class="emoji-image">
          </div>

          <span class="date">{{ post.date }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { toRaw } from 'vue';
import { nextTick } from 'vue';
import { API_BASE_URL } from '@/config.js';
import emitter from '@/eventBus';

export default {
  props: {
    post: {
      type: Object,
      required: true
    },
    accessToken: {
      type: String,
      required: true // 親からトークンを受け取る
    },
    emojiMap: {
      type: Object,
      required: true // 親から絵文字Mapを受け取る
    }
  },
  data() {
    return {
      localPost: toRaw(this.post), // propsの値をdataにコピーして保持
      replies: [],
      images: [],
      reactions: [],
      userName: "",
      userNameEn: "",
      userImage: "",
      isModalOpen: false, // モーダルが開いているか
      modalImageUrl: "", // モーダルに表示する画像のURL
      isExpanded: false,
      showExpandButton: false,
      maxHeight: 500, // imageGalleryの初期最大高
      hasImage: false,
      isUserListVisible: false,
      isScrolling: false,
      isTouchDevice: 'ontouchstart' in window, // タッチデバイスの判定
      isTapped: false, // タップ状態を管理
      hoveredUsers: [],
      hoveredReactionName: "",
      popupPosition: { top: 0, left: 0 },
      thumbnailHtml: "",
    };
  },
  inject: {
    unicodeEmojis: { default: [] },
  },
  created() {
    // 親コンポーネントから絵文字を受け取るイベントをリスン
    emitter.on('emoji-selected', this.handleEmojiSelected);
  },
  async mounted() {
    this.profile = this.fetchUserProfile();
    // 画像ファイルの URL を取得
    if (this.post.files) {
      for (const file of this.post.files) {
        await this.fetchImageSrc(file, true);
      }
      if (this.post.files.length !== 0) {
        this.hasImage = true;
        await nextTick(); // DOM が更新されるのを待つ
        const observer = new IntersectionObserver((entries) => {
          if (entries[0].isIntersecting) {
            this.checkHeight();
          }
        });

        // imageGallery が存在する場合のみ observe
        if (this.$refs.imageGallery) {
          observer.observe(this.$refs.imageGallery);
        }
      }
    }

    window.addEventListener("resize", this.checkHeight); // imageGalleryのサイズ変更(画像が呼び込まれた)検知
    window.addEventListener("scroll", this.onScroll); // スクロール検知
    // タップイベントリスナー (スマホ)
    if (this.isTouchDevice) {
      window.addEventListener("touchstart", this.onTap);
    }
    this.extractThumbnail();

    this.fetchReplies();
  },
  beforeUnmount() {
    window.removeEventListener("resize", this.checkHeight);
    window.removeEventListener("scroll", this.onScroll);

    // タップイベントリスナー (スマホ)
    if (this.isTouchDevice) {
      window.removeEventListener("touchstart", this.onTap);
    }
  },
  computed: {
    visibleImages() {
      // 表示する画像の数を決定
      return this.isExpanded ? this.images : this.images.slice(0, 4);
    },
    setGalleryClass() {
      // 画像が1枚の場合は `single-image` クラス、複数枚の場合は `multi-image` クラスを返す
      return (this.post.files && this.post.files.length == 1) ? 'single-image' : 'multi-image';
    },
    shouldShowExpandButton() {
      // 画像が複数枚かつギャラリーの高さが maxHeight を超えている場合のみ、展開ボタンを表示
      const isMultipleImages = this.post.files && this.post.files.length >= 3;
      if (isMultipleImages) {
        this.$refs.imageGallery?.offsetHeight
        // console.log(".imageGallery?.offsetHeight" + this.$refs.imageGallery?.offsetHeight);
        // console.log("this.isExpanded" + this.isExpanded);
        // console.log("this.showExpandButton" + this.showExpandButton);
        // console.log("isMultipleImages" + isMultipleImages);
      }

      return !this.isExpanded && this.showExpandButton && isMultipleImages;
    },
  },
  methods: {
    handleReactionMouseDown(reactionName, event) {
      // 長押しを検知するためのタイマーを設定
      this.reactionTimeout = setTimeout(() => {
        this.showUserList(reactionName, event);
      }, 500); // 500ms以上押された場合にユーザーリストを表示
    },
    handleReactionMouseUp() {
      // マウスボタンが離されたときにタイマーをクリア
      clearTimeout(this.reactionTimeout);
    },
    async fetchUserProfile() {
      try {
        // Flaskサーバーからprofileを取得
        const profile = await fetch(`${API_BASE_URL}/api/v1/slack/users/profile?user=${this.localPost.userId}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${toRaw(this.accessToken)}`
          }
        }).then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        }).catch(error => {
          console.error('Error fetching data:', error);
        });
        // console.log("profile:", profile);
        this.userName = profile.display_name;
        this.userNameEn = profile.real_name;
        this.userImage = profile.image_192;

      } catch (error) {
        console.error('Error fetching user profile:', error);
      }
    },
    async fetchImageSrc(file, init) {
      try {
        // Flaskサーバーから画像を取得
        // Flaskを経由するのはAuthorizationヘッダーが必要なため。imgタグでヘッダー設定できない
        // 一度画像を取得して、imgタグではキャッシュを参照している
        const url = `${API_BASE_URL}/api/v1/slack/image?url=${encodeURIComponent(init ? (file.thumb_720 ? file.thumb_720 : (file.thumb_480 ? file.thumb_480 : file.thumb_360)) : file.url_private)}&type=${encodeURIComponent(file.mimetype)}`;
        await fetch(url, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${toRaw(this.accessToken)}`
          }
        }).then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          if (init) {
            file.url = url;
            this.images.push(file);
          } else {
            this.modalImageUrl = url;
          }
        }).catch(error => {
          console.error('Error fetching data:', error);
        });
      } catch (error) {
        console.error("Error fetching image:", error);
        return file.thumb_480; // エラーが発生した場合、元のURLを表示
      }
    },
    extractThumbnail() {
      if (this.localPost.thumbnailHtmls && this.localPost.thumbnailHtmls.length > 0) {
        const attachment = this.localPost.thumbnailHtmls[0]; // 最初の添付情報を取得
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
    },
    toggleExpanded() {
      this.isExpanded = !this.isExpanded;
    },
    expandGallery() {
      this.isExpanded = true;
    },
    collapseGallery() {
      this.isExpanded = false;
    },
    async openModal(index) {
      const file = this.images[index];
      await this.fetchImageSrc(file, false);
      this.isModalOpen = true;
    },
    closeModal() {
      this.isModalOpen = false;
    },
    onScroll() {
      // ユーザーポップアップが表示されている場合は閉じる
      this.isScrolling = true;
      if (this.isUserListVisible) {
        this.isUserListVisible = false;
      }
      // 100ms 後にスクロールが止まったと判断
      clearTimeout(this.scrollTimeout);
      this.scrollTimeout = setTimeout(() => {
        this.isScrolling = false;
      }, 100);
    },
    onTap() {
      // タップ時に拡大を適用
      this.isTapped = true;
    },
    async checkHeight() {
      // DOM 更新後に高さを取得する
      await nextTick();
      const galleryHeight = this.$refs.imageGallery?.offsetHeight;
      if (galleryHeight && this.post?.files?.length) {
        console.log(this.post.files.length + " galleryHeight:" + galleryHeight);
      }
      this.showExpandButton = galleryHeight >= this.maxHeight;
    },
    async fetchReplies() {
      try {
        // Flaskサーバーから返信メッセージを取得、リアクションもここで取得
        const response = await fetch(`${API_BASE_URL}/api/v1/slack/messages/replies?channel=${this.localPost.channelId}&ts=${this.localPost.ts}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${toRaw(this.accessToken)}`
          }
        }).then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        }).catch(error => {
          console.error('Error fetching data:', error);
        });
        this.replies = await toRaw(response);

        const message = this.replies.find((msg) => msg.ts === this.localPost.ts);
        this.reactions = message?.reactions ?? [];
      } catch (error) {
        console.error('Error fetching user profile:', error);
      }
    },
    getEmojiForReaction(reactionName) {
      if (!reactionName) return

      const emoji = this.emojiMap?.find(e => e.name === reactionName);
      if (emoji) {
        return `<img src="${emoji.imageUrl}" alt="${emoji.name}" class="emoji-image" oncontextmenu="return false;">`;
      }

      // Unicode 絵文字の場合
      const unicodeEmoji = reactionName.split('::')
        .map(part => {
          const emoji = this.unicodeEmojis.find(emoji => emoji.short_name === part);
          // 絵文字が見つかった場合、HTMLエンティティに変換
          return emoji && emoji.unified ? this.convertToHtmlEntity(emoji.unified) : part;
        })
        .join(''); // 結合して返す

      if (unicodeEmoji) {
        return unicodeEmoji;
      }
      // 絵文字が見つからなかった場合、テキストとして表示
      return reactionName;
    },
    convertToHtmlEntity(unicodeString) {
      // ハイフンで分割して、各部分に &#x と ; を追加
      if (!unicodeString) return ""
      return unicodeString
        .split('-')
        .map(code => `&#x${code};`)
        .join('');
    },
    // ホバー時にユーザーリストを表示
    showUserList(reactionName, event) {
      const reaction = this.reactions.find(r => r.name === reactionName);
      this.hoveredReactionName = reaction.name;
      if (reaction && reaction.users) {
        this.hoveredUsers = reaction.users.map(user => user.name);
        this.isUserListVisible = true;

        // ホバーした要素の位置を取得
        const targetElement = event.currentTarget;
        if (!targetElement) {
          console.error('targetElement is null');
          return;
        }
        const rect = targetElement.getBoundingClientRect();

        // ポップアップの位置を設定（要素の直下に表示）
        this.popupPosition = {
          top: rect.bottom + 10, // スクロール量は考慮しない
          left: rect.left - 10,
        };
      }
    },
    // ホバーが外れたらユーザーリストを非表示にする
    hideUserList() {
      this.isUserListVisible = false;
      this.hoveredUsers = [];
    },
    openEmojiPicker(event) {
      // 絵文字ピッカーを開く(親コンポーネント呼び出し)
      this.$emit('open-picker', this.localPost.ts, event);
    },
    handleEmojiSelected(emoji) {
      console.log('Selected emoji:', emoji);
      //絵文字ピッカーで選択された絵文字をハンドルし、リアクションを追加または削除
      this.insertOrDeleteReaction(emoji.short_name, false);
    },
    async insertOrDeleteReaction(name, needDelete) {
      console.log('insertOrDeleteReaction emoji');
      // 選択した絵文字がリアクション済みか確認
      const reaction = this.existsReaction(name);
      const isReacted = reaction?.users.some(user => user.id === this.localPost.accessedId);

      if (isReacted && reaction) {
        // リアクション済みの場合削除or何もしない
        if (needDelete) {
          await this.fetchDeleteReaction(name);
          const index = this.reactions.findIndex(reaction => reaction.name === name);
          if (reaction.count == 1) {
            // リアクションのカウントが0人になったら削除
            if (index !== -1) {
              this.reactions.splice(index, 1);
              this.isUserListVisible = false;
            }
          } else {
            //リアクションのカウントが0人でなければユーザーのみ消す
            reaction.count -= 1;
            const userIndex = reaction.users.findIndex(user => user.id === this.localPost.accessedId);
            if (userIndex !== -1) {
              reaction.users.splice(userIndex, 1);
            }
            this.reactions[index] = reaction;
          }
        } else {
          // 何もせずに返却
          return;
        }
      } else {
        // リアクション追加
        // slackにリクエスト
        const successedReactName = await this.fetchAddReaction(name);
        if (successedReactName) {
          //該当の絵文字が存在すれば既存のオブジェクトに追加し、なければ新規追加
          const existingReaction = this.existsReaction(successedReactName);
          if (existingReaction) {
            existingReaction.count += 1;
            existingReaction.users.push({ id: this.localPost.accessedId, name: this.localPost.accessedName });
            const index = this.reactions.findIndex(reaction => reaction.name === name);
            this.reactions[index] = reaction;
          } else {
            this.reactions.push({
              "count": 1,
              "name": successedReactName,
              "users": [{ id: this.localPost.accessedId, name: this.localPost.accessedName }]
            });
          }
        }
      }
    },
    async fetchAddReaction(name) {
      try {
        // Flaskサーバーからprofileを取得
        await fetch(`${API_BASE_URL}/api/v1/slack/reactions/insert?channelId=${this.localPost.channelId}&name=${name}&ts=${this.localPost.ts}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${toRaw(this.accessToken)}`
          }
        }).then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return name;
        }).catch(error => {
          console.error('Error fetching data:', error);
          return null;
        });
      } catch (error) {
        console.error('Error fetching add reaction:', error);
        return null;
      }
      return name;
    },
    async fetchDeleteReaction(name) {
      try {
        // Flaskサーバーからprofileを取得
        await fetch(`${API_BASE_URL}/api/v1/slack/reactions/delete?channelId=${this.localPost.channelId}&name=${name}&ts=${this.localPost.ts}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${toRaw(this.accessToken)}`
          }
        }).then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return name;
        }).catch(error => {
          console.error('Error fetching data:', error);
          return null;
        });
      } catch (error) {
        console.error('Error fetching delete reaction:', error);
        return null;
      }
      return name;
    },
    existsReaction(name) {
      return this.reactions.find(reaction => reaction?.name === name);
    },
    checkHighlight(reaction) {
      return toRaw(reaction).users.some(user => user.id === this.localPost.accessedId);
    },
    preventContextMenu(event) {
      event.preventDefault();
    },
  }
}
</script>

<style scoped>
/* cssの共通値 */
:root {
  --user-image-size: 50px;
  /* ユーザー画像のサイズ */
  --padding: 16px;
  --border-radius: 8px;
  /* ボーダーの角の丸み */
  --box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.1);
  /* ボックスシャドウ */
}

.card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
  box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  font-size: 16px;
}

::v-deep .highlight {
  background-color: rgba(175, 245, 115, 0.308) !important;
  /* ハイライトのスタイル */
}

::v-deep .emoji-image {
  /* v-deepをつけないとv-htmlで挿入したhtmlタグにcssが適用されない */
  display: inline-block;
  vertical-align: middle;
  width: 1.5em;
  height: 1.5em;
  object-fit: contain;
  overflow-clip-margin: content-box;
  overflow: clip;
  -moz-user-select: none;
  -khtml-user-select: none;
  -webkit-user-select: none;
  user-select: none;
}

::v-deep .add-reaction-image {
  /* v-deepをつけないとv-htmlで挿入したhtmlタグにcssが適用されない */
  display: inline-block;
  vertical-align: middle;
  width: 1.5em;
  height: 1.5em;
  object-fit: contain;
  overflow-clip-margin: content-box;
  overflow: clip;
}

.add-reaction-image .emoji-image {
  /* v-deepをつけないとv-htmlで挿入したhtmlタグにcssが適用されない */
  width: 1.3em;
  height: 1.3em;
  opacity: 70%;
}

.add-reaction-image .emoji-image:hover {
  /* 画像を1倍に拡大(=reaction-item内のemojiは拡大しない) */
  transform: scale(1.2) !important;
  animation: enlarge 0.2s ease forwards !important;
}

::v-deep .emoji-image:hover {
  transform: scale(2);
  /* 画像を2倍に拡大 */
  animation: enlarge 0.1s ease forwards;
  /* enlargeアニメーションを適用 */
  z-index: 10;
  /* 他の要素よりも前に表示 */
}

::v-deep .reaction-item .emoji-image:hover {
  /* 画像を1倍に拡大(=reaction-item内のemojiは拡大しない) */
  transform: scale(1) !important;
}

/* アニメーションの定義 */
@keyframes enlarge {
  0% {
    /* 通常のサイズ */
    transform: scale(1);
  }

  100% {
    /* 1.5倍に拡大 */
    transform: scale(1.5);
  }
}

.channel-name {
  font-weight: bold;
  /* ユーザー情報との間にマージンを追加 */
  margin-bottom: 8px;
  /* テキストの色を継承 */
  color: inherit;
  text-decoration: none;
  text-align: center;
}

.header {
  height: 16px;
  display: flex;
  /* 画像とユーザー情報を上に揃える */
  align-items: flex-start;
}

.user-image {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 10px;
  display: flex;
}

.user-info {
  flex-grow: 1;
  display: flex;
  text-align: left;
  /* 垂直方向に中央揃え */
  align-items: center;
  /* 要素間のスペースを設定 */
  gap: 8px;
}

.username {
  font-weight: bold;
  font-size: 0.9em;
  color: #333;
}

.username-en {
  font-size: 0.9em;
  color: #6e6e6e;
}

.content-wrapper {
  display: flex;
  margin-top: 10px;
  align-items: flex-start;
}

.empty-space {
  width: 40px;
  flex-shrink: 0;
  border-radius: 50%;
  margin-right: 10px;
}

.content-area {
  /* 残りのスペースを使用 */
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  margin-right: 20px;
  height: auto;
}

.content {
  margin-bottom: 5px;
  text-align: left;
  /* 子要素を中央揃え */
  align-items: center;
}

::v-deep a {
  margin-bottom: 5px;
  text-align: left;
  word-break: break-all;
  /* 長いURLを折り返す */
  word-wrap: break-word;
  /* URLを強制的に折り返す */
  overflow-wrap: break-word;
  /* 改行を許可 */
  white-space: normal;
}

.detail-list {
  display: flex;
  /* 必要に応じて折り返し可能に */
  flex-wrap: wrap;
  /* アイテム間のスペース */
  gap: 10px;
  padding: 5px;
  justify-content: flex-end;
  align-items: center;
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

::v-deep .url-title {
  text-align: left;
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

.image-gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
  margin-bottom: 20px;
  /* 高さの制限を解除 */
  max-height: none;
  /* 子要素がはみ出ないように設定 */
  overflow: visible;
  transition: max-height 0.3s ease;
}

.image-gallery.expanded {
  max-height: none !important;
}

.expand-button {
  display: block;
  margin: 10px auto;
  padding: 8px 16px;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

::v-deep .image-gallery.single-image {
  display: flex;
  justify-content: center;
  align-items: center;
  max-height: 600px !important;
}

::v-deep .image-gallery.multi-image {
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  grid-auto-rows: minmax(150px, auto);
  overflow: hidden;
  max-height: 500px;
  transition: max-height 0.3s ease;
}

.image-item {
  /* 幅を45%にして2列表示 */
  flex: 1 1 45%;
  max-width: 100%;
  max-height: 60%;
  overflow: hidden;
}

.image-item img {
  width: 100%;
  height: auto;
  /* 画像の最大高さを設定 */
  max-height: 500px;
  object-fit: cover;
  /* 画像に角丸を付ける（任意） */
  border-radius: 8px;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  /* 背景を暗く */
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.modal-image {
  max-width: 90%;
  max-height: 90%;
}

.expand-button {
  position: relative;
  padding: 8px 16px;
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0), rgba(255, 255, 255, 1));
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: -80px;
  width: 100%;
  height: 60px;
}

.expand-button:hover .expand-button-context {
  padding: 10px 13px;
}

.expand-button-context {
  display: inline-block;
  background-color: rgba(93, 93, 93, 0.8);
  padding: 6px 10px;
  font-size: .8em;
  border-radius: 999px;
  box-shadow: 0 2px 6px #0003;
}

.reaction-list {
  display: flex;
  /* 必要に応じて折り返し可能に */
  flex-wrap: wrap;
  /* アイテム間のスペース */
  gap: 10px;
  padding: 5px;
}

.reaction-item {
  display: flex;
  align-items: center;
  gap: 4px;
  background-color: rgba(223, 223, 223, 0.2);
  padding: 4px 6px;
  font-size: .8em;
  border-radius: 7px;
  box-shadow: 0 2px 3px #0003;

}

/* スクロール中は拡大を無効化 */
.reaction-item:hover,
.reaction-item:active {
  transform: none;
  animation: none;
  z-index: auto;
}

.reaction-item:hover {
  transform: scale(2);
  animation: enlarge 0.1s ease forwards;
  z-index: 10;
}

/* タッチデバイスではタップ時に拡大 */
.is-tapped .reaction-item {
  transform: scale(2);
  animation: enlarge 0.1s ease forwards;
  z-index: 10;
}

.reaction-count {
  font-size: 14px;
}

.user-popup {
  position: fixed;
  padding: 10px;
  border-radius: 5px;
  z-index: 1000;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  max-width: 200px;
  font-size: 0.9em;
  background-color: rgba(255, 255, 255, 0.8);
}

.user-popup ul {
  margin: 0;
  padding: 0;
  list-style: none;
}
</style>