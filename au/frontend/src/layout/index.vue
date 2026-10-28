<template>
  <div class="app-wrapper top-layout" :style="{ '--current-color': theme }">
    <div :class="{ hasTagsView: needTagsView, fixedMain: fixedHeader }" class="main-container">
      <div :class="{ 'fixed-header': fixedHeader }">
        <navbar @setLayout="setLayout" />
        <tags-view v-if="needTagsView" />
      </div>
      <app-main />
      <settings ref="settingRef" />
    </div>
  </div>
</template>

<script setup>
import { AppMain, Navbar, Settings, TagsView } from './components'
import useSettingsStore from '@/store/modules/settings'

const settingsStore = useSettingsStore()
const theme = computed(() => settingsStore.theme)
const needTagsView = computed(() => settingsStore.tagsView)
const fixedHeader = computed(() => settingsStore.fixedHeader)

const settingRef = ref(null)
function setLayout() {
  settingRef.value?.openSetting()
}
</script>

<style lang="scss" scoped>
@import "@/assets/styles/mixin.scss";

.app-wrapper {
  @include clearfix;
  position: relative;
  width: 100%;
  min-height: 100%;
  overflow-x: hidden;
  background:
    radial-gradient(circle at 18% 8%, rgba(40, 184, 255, 0.18), transparent 30%),
    linear-gradient(180deg, #041a36 0%, #031127 46%, #020b1a 100%);
}

.main-container {
  min-height: 100%;
  margin-left: 0;
  position: relative;
}

.main-container.fixedMain {
  padding-top: 64px;
}

.main-container.fixedMain.hasTagsView {
  padding-top: 98px;
}

.fixed-header {
  position: fixed;
  top: 0;
  right: 0;
  left: 0;
  z-index: 1000;
  width: 100%;
}
</style>
