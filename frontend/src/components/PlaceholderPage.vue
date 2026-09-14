<script setup lang="ts">
defineProps<{ title: string }>()
</script>

<template>
  <div class="page-container">
    <el-result icon="info" :title="`「${title}」页面建设中`" sub-title="该页面将在后续阶段填充完整功能" />
  </div>
</template>