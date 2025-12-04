<template>
  <div v-if="isVisible" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>{{ isNewVersion ? '新しいバージョンがリリースされました！' : '更新履歴' }}</h2>
        <button class="close-button" @click="closeModal">✕</button>
      </div>
      <div class="modal-body">
        <ListItem 
          v-for="(entry, index) in changelog" 
          :key="entry.version"
          :expandable="true"
          :defaultExpanded="index === 0"
          class="changelog-entry"
        >
          <template #main>
            <div class="version-header">
              <h3 class="version-number">{{ entry.version }}</h3>
              <span class="date">{{ entry.date }}</span>
            </div>
          </template>
          <template #expanded>
            <ul class="changes-list">
              <li v-for="(change, changeIndex) in entry.changes" :key="changeIndex" :class="change.type">
                <span class="change-type">{{ getChangeTypeLabel(change.type) }}</span>
                <span class="change-description">{{ change.description }}</span>
              </li>
            </ul>
          </template>
        </ListItem>
      </div>
    </div>
  </div>
</template>

<script>
import ListItem from './ui/ListItem.vue'

export default {
  name: 'ChangelogModal',
  components: {
    ListItem
  },
  props: {
    // モーダルの表示状態
    isVisible: {
      type: Boolean,
      default: false
    },
    // 新バージョンかどうか（タイトルの表示を変える）
    isNewVersion: {
      type: Boolean,
      default: false
    },
    // 更新履歴データ
    changelog: {
      type: Array,
      default: () => []
    }
  },
  methods: {
    // モーダルを閉じる
    closeModal() {
      this.$emit('close');
    },
    // 変更タイプのラベルを取得
    getChangeTypeLabel(type) {
      const labels = {
        feature: '新機能',
        improvement: '改善',
        bugfix: 'バグ修正',
      };
      return labels[type] || '変更';
    }
  }
};
</script>

<style scoped>
/* モーダルのオーバーレイ */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: var(--z-modal-overlay);
}

/* モーダルのコンテンツ */
.modal-content {
  background-color: var(--modal-background-color);
  border-radius: var(--border-radius-lg);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: var(--shadow-xl);
  display: flex;
  flex-direction: column;
}

/* モーダルのヘッダー */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: var(--border-width) solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: var(--font-size-xl);
  color: var(--text-base-color);
  font-weight: var(--font-weight-semibold);
}

/* 閉じるボタン */
.close-button {
  background: none;
  border: none;
  font-size: var(--font-size-xl);
  color: var(--text-base-color);
  cursor: pointer;
  padding: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color var(--transition-normal);
}

.close-button:hover {
  background-color: var(--hover-color);
}

/* モーダルのボディ */
.modal-body {
  padding: var(--spacing-md) var(--spacing-lg);
  overflow-y: auto;
}

/* 更新履歴エントリー */
.changelog-entry {
  margin-bottom: var(--spacing-sm);
}

.changelog-entry:last-child {
  margin-bottom: 0;
}

/* バージョンヘッダー */
.version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.version-number {
  margin: 0;
  font-size: var(--font-size-md);
  color: var(--text-base-color);
  font-weight: var(--font-weight-semibold);
}

.date {
  font-size: var(--font-size-xs);
  color: var(--secondary-text-color);
}

/* 変更リスト */
.changes-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.changes-list li {
  display: flex;
  align-items: flex-start;
  padding: var(--spacing-xs) var(--spacing-sm);
}

/* 変更タイプラベル */
.change-type {
  flex-shrink: 0;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  margin-right: var(--spacing-sm);
  min-width: 70px;
  display: inline-block;
}

/* 変更の説明 */
.change-description {
  color: var(--text-base-color);
  line-height: 1.4;
  font-size: var(--font-size-sm);
  text-align: left;
}

/* 変更タイプ別のスタイル */
.feature .change-type {
  color: #10b981;
}

.improvement .change-type {
  color: #3b82f6;
}

.bugfix .change-type {
  color: #f59e0b;
}

.breaking .change-type {
  color: #ef4444;
}
</style>
