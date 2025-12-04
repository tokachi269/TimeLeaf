<template>
  <div :class="['list-item', { 'is-nested': isNested, 'is-expandable': expandable }]">
    <div class="list-item-content" @click="handleContentClick">
      <div v-if="expandable" class="expand-icon" @click.stop="handleExpandClick">
        {{ isExpanded ? '▼' : '▶' }}
      </div>
      <div class="list-item-main">
        <slot name="main" />
      </div>
      <div v-if="$slots.actions" class="list-item-actions">
        <slot name="actions" />
      </div>
    </div>
    <div v-if="expandable && isExpanded" class="list-item-expanded">
      <slot name="expanded" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'ListItem',
  props: {
    expandable: {
      type: Boolean,
      default: false
    },
    defaultExpanded: {
      type: Boolean,
      default: false
    },
    isNested: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      isExpanded: this.defaultExpanded
    }
  },
  methods: {
    handleExpandClick() {
      this.isExpanded = !this.isExpanded
      this.$emit('toggle', this.isExpanded)
    },
    handleContentClick(event) {
      this.$emit('click', event)
    }
  }
}
</script>

<style scoped>
.list-item {
  display: flex;
  flex-direction: column;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--border-radius-sm);
  background: var(--modal-background-color);
  transition: all var(--transition-fast);
}

.list-item:hover {
  border-color: var(--text-secound-color);
}

.list-item-content {
  display: flex;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  cursor: pointer;
  gap: var(--spacing-md);
}

.expand-icon {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xs);
  color: var(--text-secound-color);
  cursor: pointer;
  transition: color var(--transition-fast);
  user-select: none;
}

.expand-icon:hover {
  color: var(--text-base-color);
}

.list-item-main {
  flex: 1;
  min-width: 0;
}

.list-item-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.list-item-expanded {
  border-top: var(--border-width) solid var(--border-color);
  padding: var(--spacing-md);
}
</style>
