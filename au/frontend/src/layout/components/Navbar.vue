<template>
  <header class="navbar">
    <router-link class="brand" to="/index">
      <img :src="logo" class="brand-logo" alt="logo" />
      <span class="brand-title">水稻病害检测与预测平台</span>
    </router-link>

    <top-nav class="primary-menu" />

    <div class="topbar-tools">
      <router-link class="screen-return-button" to="/screen" title="返回可视化大屏">
        <span class="screen-return-icon">▣</span>
        <span>可视化大屏</span>
      </router-link>
      <div class="clock" v-if="appStore.device !== 'mobile'">
        <strong>{{ nowText }}</strong>
        <span>真实数据看板</span>
      </div>
      <el-dropdown @command="handleCommand" class="avatar-container" trigger="click">
        <div class="avatar-wrapper">
          <img :src="userStore.avatar" class="user-avatar" />
          <span class="user-name">管理员</span>
          <el-icon><caret-bottom /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <router-link to="/user/profile">
              <el-dropdown-item>个人中心</el-dropdown-item>
            </router-link>
            <el-dropdown-item command="setLayout" v-if="settingsStore.showSettings">
              <span>布局设置</span>
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <span>退出登录</span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup>
import { ElMessageBox } from 'element-plus'
import TopNav from '@/components/TopNav'
import logo from '@/assets/logo/logo.png'
import useAppStore from '@/store/modules/app'
import useUserStore from '@/store/modules/user'
import useSettingsStore from '@/store/modules/settings'

const appStore = useAppStore()
const userStore = useUserStore()
const settingsStore = useSettingsStore()
const emits = defineEmits(['setLayout'])
const nowText = ref('')

let clockTimer

function pad(value) {
  return String(value).padStart(2, '0')
}

function refreshClock() {
  const current = new Date()
  nowText.value = `${current.getFullYear()}/${pad(current.getMonth() + 1)}/${pad(current.getDate())} ${pad(current.getHours())}:${pad(current.getMinutes())}`
}

function handleCommand(command) {
  switch (command) {
    case 'setLayout':
      emits('setLayout')
      break
    case 'logout':
      logout()
      break
    default:
      break
  }
}

function logout() {
  ElMessageBox.confirm('确定注销并退出系统吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    userStore.logOut().then(() => {
      location.href = '/login'
    })
  }).catch(() => {})
}

onMounted(() => {
  refreshClock()
  clockTimer = window.setInterval(refreshClock, 60000)
})

onBeforeUnmount(() => {
  window.clearInterval(clockTimer)
})
</script>

<style lang="scss" scoped>
.navbar {
  display: grid;
  grid-template-columns: minmax(260px, 340px) minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  height: 64px;
  padding: 0 18px;

  // color: #355944;
  background: #ffffff;
  border-bottom: 1px solid #dce9df;
  box-shadow: 0 5px 18px rgba(42, 91, 57, 0.08);
}

/* =========================
   左侧平台标志
========================= */
.brand {
  display: flex;
  align-items: center;
  min-width: 0;
  height: 100%;
  color: inherit;
  text-decoration: none;
}

.brand-logo {
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  margin-right: 10px;
  object-fit: contain;
  filter: drop-shadow(0 4px 8px rgba(47, 140, 79, 0.18));
}

.brand-title {
  overflow: hidden;
  // color: #173f28;
  font-size: 21px;
  line-height: 1;
  font-weight: 800;
  white-space: nowrap;
  text-overflow: ellipsis;
  text-shadow: none;
}

/* =========================
   顶部菜单容器
========================= */
.primary-menu {
  display: flex;
  min-width: 0;
  height: 100%;
  align-items: center;
  overflow: visible;
  background: #ffffff !important;
}

/*
 * TopNav 是子组件。
 * 必须使用 :deep 才能覆盖它内部的 el-menu。
 */
:deep(.primary-menu),
:deep(.primary-menu .topmenu-container),
:deep(.primary-menu .el-menu),
:deep(.primary-menu .el-menu--horizontal),
:deep(.primary-menu.el-menu),
:deep(.primary-menu.el-menu--horizontal) {
  border: 0 !important;
  border-bottom: 0 !important;
  background: #ffffff !important;
  box-shadow: none !important;
}

/* 去掉菜单内部的深色空隙 */
:deep(.primary-menu .topmenu-container) {
  height: 100%;
  background: #ffffff !important;
}

/* 清理菜单项自身的边框、阴影 */
:deep(.primary-menu .el-menu--horizontal > .el-menu-item),
:deep(.primary-menu .el-menu--horizontal > .el-sub-menu),
:deep(
  .primary-menu
  .el-menu--horizontal
  > .el-sub-menu
  > .el-sub-menu__title
),
:deep(.primary-menu.el-menu--horizontal > .el-menu-item),
:deep(.primary-menu.el-menu--horizontal > .el-sub-menu),
:deep(
  .primary-menu.el-menu--horizontal
  > .el-sub-menu
  > .el-sub-menu__title
) {
  border: 0 !important;
  border-left: 0 !important;
  border-right: 0 !important;
  outline: 0 !important;
  box-shadow: none !important;
}

/* 清除可能绘制黑色竖条的伪元素 */
:deep(.primary-menu .el-menu--horizontal > *::before),
:deep(.primary-menu .el-menu--horizontal > *::after),
:deep(.primary-menu.el-menu--horizontal > *::before),
:deep(.primary-menu.el-menu--horizontal > *::after) {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  content: none !important;
}

/*
 * 如果 TopNav 内部插入了额外的分隔元素，
 * 只保留真正的菜单项和子菜单。
 */
:deep(
  .primary-menu
  .el-menu--horizontal
  > :not(.el-menu-item):not(.el-sub-menu)
),
:deep(
  .primary-menu.el-menu--horizontal
  > :not(.el-menu-item):not(.el-sub-menu)
) {
  display: none !important;
}

/* 普通一级菜单 */
:deep(.primary-menu .el-menu--horizontal > .el-menu-item),
:deep(
  .primary-menu
  .el-menu--horizontal
  > .el-sub-menu
  > .el-sub-menu__title
),
:deep(.primary-menu.el-menu--horizontal > .el-menu-item),
:deep(
  .primary-menu.el-menu--horizontal
  > .el-sub-menu
  > .el-sub-menu__title
) {
  height: 40px !important;
  margin: 0 2px !important;
  padding: 0 13px !important;
  line-height: 40px !important;

  color: #536a5b !important;
  border-radius: 6px !important;
  background: #ffffff !important;

  font-size: 14px !important;
  font-weight: 500 !important;

  transition:
    color 0.18s ease,
    background 0.18s ease;
}

/* 菜单悬停 */
:deep(.primary-menu .el-menu--horizontal > .el-menu-item:hover),
:deep(
  .primary-menu
  .el-menu--horizontal
  > .el-sub-menu
  > .el-sub-menu__title:hover
),
:deep(.primary-menu.el-menu--horizontal > .el-menu-item:hover),
:deep(
  .primary-menu.el-menu--horizontal
  > .el-sub-menu
  > .el-sub-menu__title:hover
) {
  color: #2f7d4a !important;
  background: #f2f8f3 !important;
}

/* 当前激活的一级菜单 */
:deep(
  .primary-menu
  .el-menu--horizontal
  > .el-menu-item.is-active
),
:deep(
  .primary-menu
  .el-menu--horizontal
  > .el-sub-menu.is-active
  > .el-sub-menu__title
),
:deep(
  .primary-menu
  .el-menu--horizontal
  > .el-sub-menu.is-opened
  > .el-sub-menu__title
),
:deep(
  .primary-menu.el-menu--horizontal
  > .el-menu-item.is-active
),
:deep(
  .primary-menu.el-menu--horizontal
  > .el-sub-menu.is-active
  > .el-sub-menu__title
),
:deep(
  .primary-menu.el-menu--horizontal
  > .el-sub-menu.is-opened
  > .el-sub-menu__title
) {
  color: #2f7d4a !important;
  border: 0 !important;
  border-radius: 6px !important;
  background: #edf7ee !important;
  box-shadow:
    inset 0 0 0 1px rgba(79, 154, 90, 0.24) !important;
}

/* 菜单图标与箭头 */
:deep(.primary-menu .el-icon),
:deep(.primary-menu svg),
:deep(.primary-menu .el-sub-menu__icon-arrow) {
  color: inherit !important;
}

/* 兼容可能存在的自定义分隔条 */
:deep(.primary-menu .nav-divider),
:deep(.primary-menu .menu-divider),
:deep(.primary-menu .topnav-divider),
:deep(.primary-menu .menu-separator),
:deep(.primary-menu .nav-separator),
:deep(.primary-menu .separator),
:deep(.primary-menu .divider) {
  display: none !important;
  width: 0 !important;
  border: 0 !important;
  background: transparent !important;
}

/* =========================
   右侧工具区域
========================= */
.topbar-tools {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  height: 100%;
}

.screen-return-button {
  display: inline-flex;
  height: 36px;
  padding: 0 12px;
  align-items: center;
  gap: 7px;
  border: 1px solid rgba(255, 255, 255, 0.32);
  border-radius: 7px;
  color: #ffffff;
  background: rgba(255, 255, 255, 0.13);
  font-size: 12px;
  font-weight: 650;
  text-decoration: none;
  white-space: nowrap;
  transition: background 0.18s ease, border-color 0.18s ease;
}

.screen-return-button:hover {
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.58);
  background: rgba(255, 255, 255, 0.22);
}

.screen-return-icon {
  font-size: 14px;
  line-height: 1;
}

.clock {
  display: grid;
  justify-items: end;
  gap: 2px;
  // color: #274a33;
  font-size: 11px;
  white-space: nowrap;

  strong {
    font-weight: 750;
  }

  span {
    color: #819286;
  }
}

.avatar-container {
  flex: 0 0 auto;
}

.avatar-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 9px 0 5px;

  border: 1px solid #d7e6db;
  border-radius: 7px;

  color: #355944;
  background: #f6faf7;
  cursor: pointer;

  transition:
    border-color 0.18s ease,
    background 0.18s ease;
}

.avatar-wrapper:hover {
  border-color: rgba(79, 154, 90, 0.4);
  background: #eef7ef;
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 5px;
  object-fit: cover;
}

.user-name {
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

/* =========================
   Element Plus 下拉菜单
   下拉层被传送到 body，必须使用 :global
========================= */
:global(.el-menu--popup) {
  padding: 6px !important;
  border: 1px solid #d8e7dc !important;
  border-radius: 7px !important;
  background: #ffffff !important;
  box-shadow: 0 14px 34px rgba(38, 78, 50, 0.16) !important;
}

:global(.el-menu--popup .el-menu) {
  border: 0 !important;
  background: #ffffff !important;
}

:global(.el-menu--popup .el-menu-item),
:global(
  .el-menu--popup
  .el-sub-menu
  > .el-sub-menu__title
) {
  min-width: 150px;
  height: 38px !important;
  margin: 2px 0 !important;
  padding: 0 13px !important;
  line-height: 38px !important;

  color: #536a5b !important;
  border: 0 !important;
  border-radius: 5px !important;
  background: #ffffff !important;
  box-shadow: none !important;
}

:global(.el-menu--popup .el-menu-item:hover),
:global(
  .el-menu--popup
  .el-sub-menu
  > .el-sub-menu__title:hover
) {
  color: #2f7d4a !important;
  background: #f1f7f2 !important;
}

/* 修复截图中“日志管理”的深蓝黑色背景 */
:global(.el-menu--popup .el-menu-item.is-active),
:global(
  .el-menu--popup
  .el-sub-menu.is-active
  > .el-sub-menu__title
),
:global(
  .el-menu--popup
  .el-sub-menu.is-opened
  > .el-sub-menu__title
) {
  color: #2f7d4a !important;
  border: 0 !important;
  background: #eaf5ec !important;
  box-shadow:
    inset 3px 0 0 #4f9a5a !important;
}

:global(.el-menu--popup .el-menu-item::before),
:global(.el-menu--popup .el-menu-item::after),
:global(.el-menu--popup .el-sub-menu::before),
:global(.el-menu--popup .el-sub-menu::after),
:global(
  .el-menu--popup
  .el-sub-menu
  > .el-sub-menu__title::before
),
:global(
  .el-menu--popup
  .el-sub-menu
  > .el-sub-menu__title::after
) {
  display: none !important;
  border: 0 !important;
  background: transparent !important;
  content: none !important;
}

/* =========================
   响应式
========================= */
@media (max-width: 1280px) {
  .navbar {
    grid-template-columns: minmax(220px, 280px) minmax(0, 1fr) auto;
    gap: 8px;
    padding: 0 10px;
  }

  .brand-title {
    font-size: 18px;
  }

  .primary-menu {
    max-width: 100%;
  }

  :deep(.primary-menu .el-menu--horizontal > .el-menu-item),
  :deep(
    .primary-menu
    .el-menu--horizontal
    > .el-sub-menu
    > .el-sub-menu__title
  ) {
    padding: 0 9px !important;
    font-size: 13px !important;
  }
}

@media (max-width: 900px) {
  .navbar {
    grid-template-columns: 1fr auto;
    height: auto;
    min-height: 64px;
    padding: 8px 10px;
  }

  .primary-menu {
    grid-column: 1 / -1;
    order: 3;
    min-height: 42px;
  }

  .clock,
  .user-name {
    display: none;
  }

  .screen-return-button {
    padding: 0 10px;
  }
}
/* “日志管理”子菜单四角清除 */
:global(.el-menu--popup .el-sub-menu),
:global(.el-menu--popup .el-sub-menu.is-active),
:global(.el-menu--popup .el-sub-menu.is-opened) {
  margin: 2px 0 !important;
  padding: 0 !important;
  border: 0 !important;
  border-radius: 5px !important;
  outline: 0 !important;
  background: transparent !important;
  background-image: none !important;
  box-shadow: none !important;
  filter: none !important;
  clip-path: none !important;
  mask: none !important;
  -webkit-mask: none !important;
}

:global(.el-menu--popup .el-sub-menu > .el-sub-menu__title) {
  position: relative !important;
  display: flex !important;
  width: 100% !important;
  min-width: 150px;
  height: 38px !important;
  margin: 0 !important;
  padding: 0 13px !important;
  align-items: center !important;

  color: #536a5b !important;
  border: 0 !important;
  border-radius: 5px !important;
  outline: 0 !important;

  background: #ffffff !important;
  background-image: none !important;

  box-shadow: none !important;
  filter: none !important;
  clip-path: none !important;
  mask: none !important;
  -webkit-mask: none !important;

  line-height: 38px !important;
}

:global(.el-menu--popup .el-sub-menu > .el-sub-menu__title:hover) {
  color: #2f7d4a !important;
  background: #f1f7f2 !important;
  box-shadow: none !important;
}

:global(.el-menu--popup .el-sub-menu.is-active > .el-sub-menu__title),
:global(.el-menu--popup .el-sub-menu.is-opened > .el-sub-menu__title),
:global(.el-menu--popup .el-sub-menu > .el-sub-menu__title:focus),
:global(.el-menu--popup .el-sub-menu > .el-sub-menu__title:focus-visible) {
  color: #2f7d4a !important;
  border: 0 !important;
  outline: 0 !important;
  background: #eaf5ec !important;
  background-image: none !important;
  box-shadow: none !important;
}

:global(.el-menu--popup .el-sub-menu::before),
:global(.el-menu--popup .el-sub-menu::after),
:global(.el-menu--popup .el-sub-menu > .el-sub-menu__title::before),
:global(.el-menu--popup .el-sub-menu > .el-sub-menu__title::after) {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
  border: 0 !important;
  background: none !important;
  box-shadow: none !important;
  content: none !important;
}
</style>
