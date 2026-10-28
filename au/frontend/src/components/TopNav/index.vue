<template>
  <el-menu
    class="topmenu-container agri-top-menu"
    :default-active="activeMenu"
    mode="horizontal"
    :ellipsis="false"
    @select="handleSelect"
  >
    <top-menu-item
      v-for="item in topMenus"
      :key="item.fullPath"
      :item="item"
    />
  </el-menu>
</template>

<script setup>
import { isHttp } from '@/utils/validate'
import usePermissionStore from '@/store/modules/permission'
import TopMenuItem from './TopMenuItem.vue'

const permissionStore = usePermissionStore()
const route = useRoute()
const router = useRouter()
const routers = computed(() => {
  const sidebarRouters = permissionStore.sidebarRouters || []
  return sidebarRouters.length ? sidebarRouters : permissionStore.topbarRouters
})

const topMenus = computed(() => {
  return routers.value
    .filter(item => item && item.hidden !== true)
    .map(item => normalizeMenuRoute(item))
    .filter(Boolean)
})

const flatMenus = computed(() => {
  return collectLeafMenus(topMenus.value)
})

const activeMenu = computed(() => {
  const currentPath = route.path
  const matched = flatMenus.value
    .filter(item => currentPath === item.fullPath || currentPath.startsWith(`${item.fullPath}/`))
    .sort((a, b) => b.fullPath.length - a.fullPath.length)

  return matched[0]?.fullPath || currentPath
})

function normalizeMenuRoute(item, parentPath = '') {
  const fullPath = resolveRoutePath(parentPath, item.path)
  const children = (item.children || [])
    .filter(child => child && child.hidden !== true)
    .map(child => normalizeMenuRoute(child, fullPath))
    .filter(Boolean)

  if (children.length === 1 && !item.alwaysShow && !children[0].children.length) {
    return children[0]
  }

  if (!item.meta && !children.length) {
    return null
  }

  return {
    title: item.meta?.title || item.name || fullPath,
    icon: item.meta?.icon,
    fullPath,
    query: item.query,
    children
  }
}

function collectLeafMenus(items) {
  return items.flatMap(item => item.children.length ? collectLeafMenus(item.children) : [item])
}

function resolveRoutePath(parentPath, routePath) {
  if (isHttp(routePath)) {
    return routePath
  }
  if (!routePath) {
    return parentPath || '/'
  }
  if (routePath.startsWith('/')) {
    return routePath
  }
  const parent = parentPath && parentPath !== '/' ? parentPath : ''
  return `${parent}/${routePath}`.replace(/\/+/g, '/')
}

function handleSelect(key) {
  if (!key || key === route.path) {
    return
  }

  if (isHttp(key)) {
    window.open(key, '_blank')
    return
  }

  const routeMenu = flatMenus.value.find(item => item.fullPath === key)
  if (routeMenu?.query) {
    router.push({ path: key, query: JSON.parse(routeMenu.query) })
    return
  }

  router.push({ path: key })
}
</script>

<style lang="scss">
.agri-top-menu.el-menu--horizontal {
  --el-menu-bg-color: #ffffff;
  --el-menu-text-color: #3f5948;
  --el-menu-hover-bg-color: #edf5ee;
  --el-menu-hover-text-color: #24653b;
  --el-menu-active-color: #24653b;
  --el-menu-border-color: transparent;
  display: flex;
  align-items: center;
  min-width: 0;
  height: 64px;
  border: 0 !important;
  border-bottom: 0 !important;
  background: #ffffff !important;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
  box-shadow: none !important;

  &::-webkit-scrollbar {
    display: none;
  }
}

.agri-top-menu.el-menu--horizontal > .el-sub-menu {
  height: 40px !important;
  margin: 0 2px !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

.agri-top-menu.el-menu--horizontal > .el-menu-item,
.agri-top-menu.el-menu--horizontal > .el-sub-menu > .el-sub-menu__title {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 40px !important;
  line-height: 40px !important;
  margin: 0;
  padding: 0 13px !important;
  border: 1px solid transparent !important;
  border-bottom: 0 !important;
  border-radius: 6px;
  color: #3f5948 !important;
  background: #ffffff !important;
  font-size: 14px;
  white-space: nowrap;
  letter-spacing: 0;
  outline: 0 !important;
  box-shadow: none !important;
  transition: color 0.2s, border-color 0.2s, background 0.2s, box-shadow 0.2s;
}

.agri-top-menu.el-menu--horizontal > .el-menu-item.is-active,
.agri-top-menu.el-menu--horizontal > .el-sub-menu.is-active > .el-sub-menu__title,
.agri-top-menu.el-menu--horizontal > .el-sub-menu.is-opened > .el-sub-menu__title {
  color: #24653b !important;
  border-color: rgba(47, 125, 74, 0.28) !important;
  background: #edf5ee !important;
  box-shadow: inset 0 0 0 1px rgba(47, 125, 74, 0.08) !important;
}

.agri-top-menu.el-menu--horizontal > .el-menu-item:not(.is-disabled):focus,
.agri-top-menu.el-menu--horizontal > .el-menu-item:not(.is-disabled):hover,
.agri-top-menu.el-menu--horizontal > .el-sub-menu:not(.is-disabled):focus,
.agri-top-menu.el-menu--horizontal > .el-sub-menu:not(.is-disabled):hover,
.agri-top-menu.el-menu--horizontal > .el-sub-menu > .el-sub-menu__title:focus,
.agri-top-menu.el-menu--horizontal > .el-sub-menu > .el-sub-menu__title:hover {
  color: #24653b !important;
  border-color: rgba(47, 125, 74, 0.22) !important;
  background: #f3f8f2 !important;
  outline: 0 !important;
  box-shadow: none !important;
}

.agri-top-menu.el-menu--horizontal > .el-menu-item::before,
.agri-top-menu.el-menu--horizontal > .el-menu-item::after,
.agri-top-menu.el-menu--horizontal > .el-sub-menu::before,
.agri-top-menu.el-menu--horizontal > .el-sub-menu::after,
.agri-top-menu.el-menu--horizontal > .el-sub-menu > .el-sub-menu__title::before,
.agri-top-menu.el-menu--horizontal > .el-sub-menu > .el-sub-menu__title::after {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  content: none !important;
}

.agri-top-menu .svg-icon {
  flex: 0 0 auto;
  margin-right: 5px;
}

.agri-top-menu .el-sub-menu .el-sub-menu__icon-arrow {
  position: static;
  margin-top: 0;
  margin-left: 7px;
  color: #718177;
}

.agri-top-menu-popper {
  border: 1px solid #dce8dc !important;
  border-radius: 4px !important;
  background: #ffffff !important;
  box-shadow: 0 14px 34px rgba(43, 87, 55, 0.14);

  .el-menu {
    min-width: 180px;
    padding: 6px;
    border: none;
    background: transparent;
  }

  .el-menu-item {
    height: 36px;
    line-height: 36px;
    margin: 2px 0;
    border-radius: 4px;
    color: #3f5948;
  }

  .el-sub-menu__title {
    height: 36px;
    line-height: 36px;
    margin: 2px 0;
    border-radius: 4px;
    color: #3f5948;

    &:hover,
    &:focus {
      color: #24653b;
      background: #edf5ee;
    }
  }

  .el-menu-item.is-active,
  .el-menu-item:hover,
  .el-menu-item:focus {
    color: #24653b;
    background: #edf5ee;
  }

  .svg-icon {
    margin-right: 6px;
  }
}
</style>
