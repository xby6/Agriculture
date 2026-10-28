<template>
  <section class="app-main">
    <div class="page-background-decoration decoration-left"></div>
    <div class="page-background-decoration decoration-right"></div>

    <div
      v-if="showPlatformRibbon"
      class="agri-platform-ribbon"
      role="region"
      aria-label="当前平台模块"
    >
      <div class="ribbon-leading">
        <div class="ribbon-mark" aria-hidden="true">
          <span>稻</span>
        </div>

        <div class="ribbon-copy">
          <div class="ribbon-title-row">
            <strong>{{ route.meta.title || '农业平台管理' }}</strong>
            <span class="ribbon-badge">智慧农业</span>
          </div>

          <span class="ribbon-description">
            基地、地块、环境、病害、遥感、农事与模型服务统一管理
          </span>
        </div>
      </div>

      <div class="ribbon-status">
        <span class="status-indicator">
          <i></i>
        </span>
        <div class="status-copy">
          <strong>服务运行正常</strong>
          <small>农业生产数据服务已连接</small>
        </div>
      </div>
    </div>

    <div class="route-content">
      <router-view v-slot="{ Component, route: viewRoute }">
        <transition name="fade-transform" mode="out-in">
          <keep-alive :include="tagsViewStore.cachedViews">
            <component
              v-if="!viewRoute.meta.link"
              :is="Component"
              :key="viewRoute.path"
            />
          </keep-alive>
        </transition>
      </router-view>

      <iframe-toggle />
    </div>
  </section>
</template>

<script setup>
import iframeToggle from './IframeToggle/index'
import useTagsViewStore from '@/store/modules/tagsView'

const route = useRoute()
const tagsViewStore = useTagsViewStore()

const showPlatformRibbon = computed(() => {
  const businessPrefixes = [
    '/index',
    '/agriculture',
    '/map',
    '/node',
    '/file',
    '/container',
    '/task'
  ]

  return !businessPrefixes.some(
    prefix =>
      route.path === prefix ||
      route.path.startsWith(`${prefix}/`)
  )
})

onMounted(() => {
  addIframe()
})

watch(
  () => route.fullPath,
  () => {
    addIframe()
  }
)

function addIframe() {
  if (route.meta.link) {
    useTagsViewStore().addIframeView(route)
  }
}
</script>

<style lang="scss" scoped>
.app-main {
  position: relative;
  width: 100%;
  min-height: calc(100vh - 64px);
  overflow-x: hidden;
  overflow-y: auto;

  color: #213b2b;

  background:
    radial-gradient(
      circle at 8% 4%,
      rgba(245, 249, 246, 0.1),
      transparent 26%
    ),
    radial-gradient(
      circle at 94% 12%,
      rgba(96, 157, 174, 0.08),
      transparent 24%
    ),
    linear-gradient(
      180deg,
      #f9fbf9 0%,
      #f3f7f3 44%,
      #edf3ee 100%
    );
}

.app-main,
.app-main *,
.app-main *::before,
.app-main *::after {
  box-sizing: border-box;
}

/* 页面背景轻装饰 */
.page-background-decoration {
  position: absolute;
  z-index: 0;
  border-radius: 50%;
  pointer-events: none;
  filter: blur(90px);
  opacity: 0.15;
}

.decoration-left {
  top: 140px;
  left: -140px;
  width: 280px;
  height: 280px;
  background: #75b681;
}

.decoration-right {
  top: 520px;
  right: -170px;
  width: 320px;
  height: 320px;
  background: #75aab7;
}

.route-content {
  position: relative;
  z-index: 1;
  min-width: 0;
}

/* =========================================================
   平台模块提示条
========================================================= */
.agri-platform-ribbon {
  position: relative;
  z-index: 2;

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22px;

  margin: 16px 18px 0;
  padding: 14px 16px;

  overflow: hidden;

  border: 1px solid rgba(80, 139, 94, 0.18);
  border-radius: 14px;

  background:
    linear-gradient(
      110deg,
      rgba(255, 255, 255, 0.97),
      rgba(247, 251, 248, 0.95)
    );

  box-shadow:
    0 10px 30px rgba(37, 77, 49, 0.07),
    0 1px 2px rgba(37, 77, 49, 0.04);

  backdrop-filter: blur(14px);
}

.agri-platform-ribbon::before {
  position: absolute;
  top: 10px;
  bottom: 10px;
  left: 0;

  width: 4px;

  border-radius: 0 4px 4px 0;

  content: "";

  background:
    linear-gradient(
      180deg,
      #55a36a 0%,
      #327c4b 100%
    );
}

.agri-platform-ribbon::after {
  position: absolute;
  top: -58px;
  right: 120px;

  width: 180px;
  height: 180px;

  border: 1px solid rgba(78, 151, 95, 0.07);
  border-radius: 50%;

  content: "";
  pointer-events: none;
}

.ribbon-leading {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 13px;
}

.ribbon-mark {
  position: relative;

  display: grid;
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  place-items: center;

  overflow: hidden;

  color: #ffffff;

  border: 1px solid rgba(255, 255, 255, 0.62);
  border-radius: 12px;

  background:
    linear-gradient(
      145deg,
      #58a76d 0%,
      #3d8c57 55%,
      #2f7547 100%
    );

  box-shadow:
    0 7px 16px rgba(47, 117, 71, 0.20),
    inset 0 1px 0 rgba(255, 255, 255, 0.32);
}

.ribbon-mark::before {
  position: absolute;
  top: -13px;
  right: -13px;

  width: 34px;
  height: 34px;

  border: 1px solid rgba(255, 255, 255, 0.24);
  border-radius: 50%;

  content: "";
}

.ribbon-mark span {
  position: relative;
  z-index: 1;

  font-size: 19px;
  line-height: 1;
  font-weight: 800;

  text-shadow: 0 2px 5px rgba(28, 75, 42, 0.30);
}

.ribbon-copy {
  min-width: 0;
}

.ribbon-title-row {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 9px;
}

.ribbon-title-row strong {
  min-width: 0;
  overflow: hidden;

  color: #1c3b27;

  font-size: 16px;
  line-height: 1.25;
  font-weight: 780;

  white-space: nowrap;
  text-overflow: ellipsis;
}

.ribbon-badge {
  flex: 0 0 auto;
  padding: 4px 8px;

  color: #39784d;

  border: 1px solid #cee1d2;
  border-radius: 999px;

  background: #eef7f0;

  font-size: 9px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 0.35px;
}

.ribbon-description {
  display: block;

  margin-top: 5px;

  overflow: hidden;

  color: #75887a;

  font-size: 11px;
  line-height: 1.35;
  font-weight: 500;

  white-space: nowrap;
  text-overflow: ellipsis;
}

.ribbon-status {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 9px;

  min-width: 182px;
  padding: 8px 11px;

  border: 1px solid #d4e5d8;
  border-radius: 10px;

  background: rgba(240, 248, 242, 0.90);
}

.status-indicator {
  display: grid;
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  place-items: center;

  border: 1px solid #c6dfcd;
  border-radius: 8px;

  background: #e8f5eb;
}

.status-indicator i {
  width: 8px;
  height: 8px;

  border-radius: 50%;

  background: #48a363;

  box-shadow:
    0 0 0 4px rgba(72, 163, 99, 0.12),
    0 0 10px rgba(72, 163, 99, 0.28);

  animation: status-pulse 2.2s ease-in-out infinite;
}

.status-copy {
  min-width: 0;
}

.status-copy strong,
.status-copy small {
  display: block;
  white-space: nowrap;
}

.status-copy strong {
  color: #2f6843;
  font-size: 11px;
  line-height: 1.2;
  font-weight: 750;
}

.status-copy small {
  margin-top: 3px;
  color: #7d8f82;
  font-size: 9px;
  line-height: 1.2;
}

@keyframes status-pulse {
  0%,
  100% {
    opacity: 0.62;
    transform: scale(0.92);
  }

  50% {
    opacity: 1;
    transform: scale(1.08);
  }
}

/* =========================================================
   页面切换动画
========================================================= */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition:
    opacity 0.18s ease,
    transform 0.18s ease;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateY(5px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateY(-3px);
}

/* =========================================================
   响应式
========================================================= */
@media (max-width: 1100px) {
  .agri-platform-ribbon {
    gap: 14px;
  }

  .ribbon-status {
    min-width: auto;
  }

  .status-copy small {
    display: none;
  }
}

@media (max-width: 760px) {
  .agri-platform-ribbon {
    margin: 12px 12px 0;
    padding: 12px 13px;
    border-radius: 12px;
  }

  .ribbon-mark {
    width: 38px;
    height: 38px;
    flex-basis: 38px;
    border-radius: 10px;
  }

  .ribbon-title-row strong {
    font-size: 14px;
  }

  .ribbon-description,
  .ribbon-badge,
  .ribbon-status {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .status-indicator i,
  .fade-transform-enter-active,
  .fade-transform-leave-active {
    animation: none !important;
    transition: none !important;
  }
}
</style>

<style lang="scss">
.el-popup-parent--hidden {
  .fixed-header {
    padding-right: 6px;
  }
}

/* 全局滚动条统一为浅色农业风 */
::-webkit-scrollbar {
  width: 7px;
  height: 7px;
}

::-webkit-scrollbar-track {
  background: #eef3ef;
}

::-webkit-scrollbar-thumb {
  border: 2px solid #eef3ef;
  border-radius: 999px;
  background: #a8c6b0;
}

::-webkit-scrollbar-thumb:hover {
  background: #79a987;
}

/* Firefox */
* {
  scrollbar-width: thin;
  scrollbar-color: #a8c6b0 #eef3ef;
}
</style>
