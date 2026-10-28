<template>
  <el-sub-menu
    v-if="item.children && item.children.length"
    :index="item.fullPath"
    popper-class="agri-top-menu-popper"
  >
    <template #title>
      <svg-icon v-if="item.icon && item.icon !== '#'" :icon-class="item.icon" />
      <span>{{ item.title }}</span>
    </template>
    <top-menu-item
      v-for="child in item.children"
      :key="child.fullPath"
      :item="child"
    />
  </el-sub-menu>

  <el-menu-item v-else :index="item.fullPath">
    <svg-icon v-if="item.icon && item.icon !== '#'" :icon-class="item.icon" />
    <span>{{ item.title }}</span>
  </el-menu-item>
</template>

<script setup name="TopMenuItem">
defineProps({
  item: {
    type: Object,
    required: true
  }
})
</script>
