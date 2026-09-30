<template>
  <div class="field">
    <div class="field-label">{{ label }}</div>
    <div class="field-control">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string }>()
</script>

<style scoped>
.field-label {
  font-size: 11px;
  color: #9a9a9a;
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
