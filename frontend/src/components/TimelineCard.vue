<template>
  <div class="timeline-card">
    <div v-if="canDisplayPost" class="card">
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

          <!-- URLのサムネイル -->
          <div v-if="thumbnailHtml" class="url-preview-container" v-html="thumbnailHtml"></div> <!-- サムネイル表示 -->

          <!-- 画像一覧 -->
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

          <!-- リアクション一覧 -->
          <div class="reaction-list">
            <div v-for="reaction in reactions" :key="reaction.name" class="reaction-item"
              :class="{ 'highlight': checkHighlight(reaction) }"
              @mouseenter="showUserList(reaction, reaction.name, $event)" @mouseleave="hideUserList"
              @click="insertOrDeleteReaction(reaction.name, localPost.ts, localPost.ts, true)"
              @mousedown="handleReactionMouseDown(reaction, reaction.name, $event)" @mouseup="handleReactionMouseUp"
              @touchstart="handleReactionMouseDown(reaction, reaction.name, $event)" @touchend="handleReactionMouseUp">
              <span v-html="getEmojiForReaction(reaction.name)"></span>
              <span class="reaction-count">{{ reaction.count }}</span>
            </div>
            <div v-if="reactions.length != 0" @click="openEmojiPicker(this.localPost.ts, $event)" class="reaction-item">
              <img src="./../assets/emoji-add.png" alt="Add Reaction" class="emoji-image">
            </div>
            <br>
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
          <!-- スレッド表示/非表示ボタン -->
          <div v-if="replies && replies.length > 1" class="thread-container">

            <div class="thread-toggle">
              <button @click="toggleThread" v-if="!showThread">スレッドを表示</button>
              <button @click="toggleThread" v-if="showThread">スレッドを閉じる</button>
            </div>
            <!-- スレッドの内容を表示 -->
            <transition @after-leave="adjustScroll">
              <div v-if="showThread && replies && replies.length > 1">
                <div class="thread-content">
                  <div v-for="(reply, index) in replies" :key="reply.ts" class="thread-reply">
                    <div v-if="index > 0">
                      <div class="header">
                        <img :src="userImage" alt="User Image" class="user-image user-reply-image" />
                        <div class="user-info">
                          <span class="username">{{ reply.user_real_name }}</span>
                          <span class="username-en">{{ reply.user_name }}</span>
                        </div>
                      </div>
                      <div class="content-wrapper">
                        <div class="thread-empty-space"></div>
                        <div class="content-area">
                          <div class="content" v-html="reply.text"></div>
                        </div>
                      </div>

                      <!-- 画像一覧 -->
                      <div v-if="reply.files">
                        画像表示は現在未対応です

                        <!-- <div ref="imageGallery" class="image-gallery"
                        :class="[setGalleryClass, { 'expanded': isExpanded }]">
                        <div v-for="(file, index) in  reply.files.slice(0, 4)" :key="index" class="image-item">
                          <img :src="fetchImageSrcReply(file, true)" :alt="file.name" class="image" @click="openModal(index)" crossorigin="anonymous" />
                        </div>
                      </div>
                      <button v-if="shouldShowExpandButton" class="expand-button" @click="toggleExpanded">
                        <span class="expand-button-context">もっと見る</span>
                      </button> -->
                      </div>
                      <!-- リアクション一覧 -->
                      <div class="reaction-list">
                        <div v-for="reaction in reply.reactions" :key="reaction.name" class="reaction-item"
                          :class="{ 'highlight': checkHighlight(reaction) }"
                          @mouseenter="showUserList(reaction, reaction.name, $event)" @mouseleave="hideUserList"
                          @click="insertOrDeleteReaction(reaction.name, reply.thread_ts, reply.ts, true)"
                          @mousedown="handleReactionMouseDown(reaction.name, $event)" @mouseup="handleReactionMouseUp"
                          @touchstart="handleReactionMouseDown(reaction.name, $event)"
                          @touchend="handleReactionMouseUp">
                          <span v-html="getEmojiForReaction(reaction.name)"></span>
                          <span class="reaction-count">{{ reaction.count }}</span>
                        </div>
                        <div v-if="reactions.length != 0" @click="openEmojiPicker(reply.ts, $event)"
                          class="reaction-item">
                          <img src="./../assets/emoji-add.png" alt="Add Reaction" class="emoji-image">
                        </div>
                        <br>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="thread-toggle">
                  <button @click="toggleThread">スレッドを閉じる</button>
                </div>
              </div>
            </transition>

          </div>
          <div class="detail-list">
            <div v-if="reactions.length == 0" @click="openEmojiPicker($event)" class="add-reaction-image">
              <img src="./../assets/emoji-add.png" alt="Add Reaction" class="emoji-image">
            </div>
            <div @click="showReplyBox = true" class="add-reaction-image">
              <img src="./../assets/reply.png" alt="Add Reaction" class="emoji-image">
            </div>
            <span class="date">{{ post.date }}</span>
          </div>
          <!-- テキストボックスと閉じるボタン -->
          <div v-if="showReplyBox" class="reply-box">
            <textarea v-model="replyText" placeholder="返信を入力..."></textarea>
            <div class="reply-button-list">
              <button @click="fetchAddReply" class="button-submit reply-box-color">送信</button>
              <input type="checkbox" id="replyBroadcast" v-model="replyBroadcast" />
              <label for="replyBroadcast">チャンネルにも投稿</label>
              <button @click="showReplyBox = false" class="button-submit reply-close-box-color">閉じる</button>
            </div>
          </div>
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
      message: {},
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
      canDisplayPost: false,
      showReplyBox: false,
      replyText: '', // テキストボックスの入力内容を管理
      replyBroadcast: false, // チェックボックスの状態を管理
      showThread: false, // スレッドの表示/非表示を管理
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
    await this.fetchReplies();
    //スレッド投稿の場合は表示しないが、スレッドブロードキャストの場合は表示する
    //thread_ts がある、親投稿じゃない、スレッドブロードキャストじゃないときにスレッド内の投稿と判断
    this.message = this.replies?.find((msg) => msg.ts === this.localPost.ts);
    this.canDisplayPost = !this.message ? false : !(this.message && this.message.thread_ts && this.message.thread_ts != this.message.ts && this.message?.subtype !== "thread_broadcast");

    if (this.message && this.message.thread_ts && this.message.thread_ts == this.message.ts) {
      console.log(this.message);
      console.log(this.replies);
    }
    this.extractThumbnail();

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
    adjustScroll() {
      this.$nextTick(() => {
        const cardElement = this.$el;
        const targetPosition = cardElement.getBoundingClientRect().top + window.scrollY;
        const startPosition = window.scrollY;
        const distance = targetPosition - startPosition;
        const duration = 150; // スクロールの速度（ミリ秒）
        let startTime = null;

        function animation(currentTime) {
          if (startTime === null) startTime = currentTime;
          const timeElapsed = currentTime - startTime;
          const run = easeInOutQuad(timeElapsed, startPosition, distance, duration);
          window.scrollTo(0, run);
          if (timeElapsed < duration) requestAnimationFrame(animation);
        }

        function easeInOutQuad(t, b, c, d) {
          t /= d / 2;
          if (t < 1) return c / 2 * t * t + b;
          t--;
          return -c / 2 * (t * (t - 2) - 1) + b;
        }

        requestAnimationFrame(animation);
      });
    },
    toggleThread() {
      this.showThread = !this.showThread;
    },
    handleReactionMouseDown(reaction, reactionName, event) {
      // 長押しを検知するためのタイマーを設定
      this.reactionTimeout = setTimeout(() => {
        this.showUserList(reaction, reactionName, event);
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
    async fetchImageSrcReply(file, init) {
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
            return url;
          } else {
            //  this.modalImageUrl = url;
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
          return;
        }
      }
      this.localPost.urls.forEach(url => {
        if (url.includes("open.spotify.com")) {
          const trackId = this.extractTrackId(url);
          if (trackId) {
            // サムネイル用HTMLを作成
            this.thumbnailHtml = `
                <iframe style="border-radius:12px" src="https://open.spotify.com/embed/${url.includes("track") ? "track" : url.includes("album") ? "album" : "playlist"}/${trackId}?utm_source=generator" width="100%" height="352" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy"></iframe>
              `;
          }
        } else if (url.includes("youtube.com")) {
          const videoId = this.extractTrackId(url);
          if (videoId) {
            // YouTube埋め込み用HTMLを作成
            this.thumbnailHtml = `
                <iframe width="100%" height="315" src="https://www.youtube.com/embed/${videoId}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
              `;
          }
        } else if (url.includes("youtu.be")) {
        //   const urlObj = new URL(url);
        //   const videoId = urlObj.pathname.split('/')[1];
        //   const siValue = urlObj.searchParams.get('si');

        //   if (siValue) {
        //     // YouTube埋め込み用HTMLを作成
        //     this.thumbnailHtml = `
        //         <iframe width="100%" height="315" src="https://www.youtube.com/embed/${videoId}?si=${siValue}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        //       `;
        //   }
         }
      });
    },
    extractTrackId(url) {
      const match = url.match(/\/([^\\/?]+)\?/);
      return match ? match[1] : null;
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
          this.replies = null;
          console.error('Error fetching data:', error);
          return;
        });
        this.replies = await toRaw(response);

        const message = this.replies?.find((msg) => msg.ts === this.localPost.ts);
        this.reactions = message?.reactions ?? [];
      } catch (error) {
        this.replies = null;
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
    showUserList(reaction, reactionName, event) {
      this.hoveredReactionName = reactionName;
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
    openEmojiPicker(ts, event) {
      // 絵文字ピッカーを開く(親コンポーネント呼び出し)
      this.$emit('open-picker', this.localPost.ts, ts, event);
    },
    handleEmojiSelected(emoji, parentTs, threadTs) {
      console.log('Selected emoji:', emoji);
      //絵文字ピッカーで選択された絵文字をハンドルし、リアクションを追加または削除
      this.insertOrDeleteReaction(emoji.short_name, parentTs, threadTs, false);
    },
    async insertOrDeleteReaction(name, parentTs, threadTs, needDelete) {
      console.log('insertOrDeleteReaction emoji');
      // 選択した絵文字がリアクション済みか確認
      let reaction = this.existsReaction(name, parentTs === threadTs ? parentTs : threadTs);
      let reactionList = this.existsReactionsList(parentTs === threadTs ? parentTs : threadTs);
      const isReacted = reaction?.users.some(user => user.id === this.localPost.accessedId);

      if (isReacted && reaction) {
        // リアクション済みの場合削除or何もしない
        if (needDelete) {
          await this.fetchDeleteReaction(name, parentTs);
          const index = reactionList?.findIndex(reaction => reaction.name === name);
          if (reaction.count == 1) {
            // リアクションのカウントが0人になったら削除
            if (index !== -1) {
              reactionList.splice(index, 1);
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
        const successedReactName = await this.fetchAddReaction(name, parentTs);
        if (successedReactName) {
          //該当の絵文字が存在すれば既存のオブジェクトに追加し、なければ新規追加
          const existingReaction = this.existsReaction(successedReactName, parentTs === threadTs ? parentTs : threadTs);
          if (existingReaction) {
            existingReaction.count += 1;
            existingReaction.users.push({ id: this.localPost.accessedId, name: this.localPost.accessedName });
            const index = reactionList.findIndex(reaction => reaction.name === name);
            reactionList[index] = reaction;
          } else {
            if (parentTs === threadTs) {
              this.reactions.push({
                "count": 1,
                "name": successedReactName,
                "users": [{ id: this.localPost.accessedId, name: this.localPost.accessedName }]
              });
            } else if (reactionList) {
              reactionList.push({
                "count": 1,
                "name": successedReactName,
                "users": [{ id: this.localPost.accessedId, name: this.localPost.accessedName }]
              });
            } else {
              const message = this.replies?.find((msg) => msg.ts === (parentTs === threadTs ? parentTs : threadTs));
              message.reactionList = {
                "count": 1,
                "name": successedReactName,
                "users": [{ id: this.localPost.accessedId, name: this.localPost.accessedName }]
              };
            }
          }
        }
      }
    },
    existsReaction(name, ts) {
      if (this.localPost.ts === ts) {
        return this.reactions.find(reaction => reaction?.name === name);
      } else {
        const message = this.replies?.find((msg) => msg.ts === ts);
        return message?.reactions?.find(reaction => reaction?.name === name);
      }
    },
    existsReactionsList(ts) {
      if (this.localPost.ts === ts) {
        return this.reactions;
      } else {
        const message = this.replies?.find((msg) => msg.ts === ts);
        return message?.reactions;
      }
    },
    async fetchAddReaction(name, ts) {
      try {
        // Flaskサーバーからprofileを取得
        await fetch(`${API_BASE_URL}/api/v1/slack/reactions/insert?channelId=${this.localPost.channelId}&name=${name}&ts=${ts}`, {
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
    async fetchDeleteReaction(name, ts) {
      try {
        // Flaskサーバーからprofileを取得
        await fetch(`${API_BASE_URL}/api/v1/slack/reactions/delete?channelId=${this.localPost.channelId}&name=${name}&ts=${ts}`, {
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
    async fetchAddReply() {
      try {
        // Flaskサーバーからprofileを取得
        const response = await fetch(`${API_BASE_URL}/api/v1/slack/messages/reply?channelId=${this.localPost.channelId}&text=${this.replyText}&thread_ts=${(this.message && this.message?.thread_ts) ? this.message.thread_ts : this.localPost.ts}&reply_broadcast=${this.replyBroadcast}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${toRaw(this.accessToken)}`
          }
        }).then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          this.showReplyBox = false;
          this.replyText = "";
          return response;
        }).catch(error => {
          console.error('Error fetching data:', error);
          return;
        });
        const data = await response.json();
        const rep = toRaw(data);
        this.replies.push(rep);
        return rep;
      } catch (error) {
        console.error('Error fetching add reaction:', error);
        return;
      }

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

.user-reply-image {
  width: 20px;
  height: 20px;
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
  gap: 20px;
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
  user-select: none;
  /* 文字を選択できなくする */
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

.reply-box {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.reply-box textarea {
  width: 100%;
  height: 60px;
  margin-bottom: 10px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
  resize: none;
}

.reply-button-list {
  padding: 5px;
  align-items: center;
  justify-content: center;
}

.button-submit {
  flex: auto;
  gap: 30px;
  padding: 8px 16px;
  background-color: rgb(148, 202, 104);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  margin-right: 30px;
  transition: background-color 0.3s ease;
}

.reply-box-color {
  background-color: rgb(148, 202, 104);
}

.reply-box-color button:hover {
  background-color: rgb(132, 181, 91);
}

.reply-close-box-color {
  margin-left: 50px;
  background-color: rgba(177, 177, 177);
}

.reply-close-box-color button:hover {
  background-color: rgb(125, 125, 125);
}

.thread-container {
  margin: 10px;
}

.thread-empty-space {
  width: 20px;
  flex-shrink: 0;
  border-radius: 50%;
  margin-right: 10px;
}

.thread-reply {
  margin-bottom: 10px;
}

.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.5s ease;
}

.slide-fade-enter,
.slide-fade-leave-to

/* .slide-fade-leave-active in <2.1.8 */
  {
  transform: translateY(10px);
  opacity: 0;
}

.thread-content {
  flex: 1;
  padding: 5px;
  border-top: 1px solid #ccc;
  background-color: #f9f9f9;
}

.thread-reply {
  margin-bottom: 10px;
}

.thread-toggle {
  user-select: none;
  display: flex;
  /* border-bottom: 2px solid #ccc; */
}

.thread-toggle button {
  flex: 1;
  background-color: #d1d1d1 !important;
  border: none;
  font-size: 1em;
  cursor: pointer;
  text-align: center;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.thread-toggle button:hover {
  background-color: #8e8e8e !important;
}
</style>