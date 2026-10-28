<template>
  <section class="agri-page-header">
    <div class="agri-page-header__main">
      <div class="agri-page-header__icon">
        <el-icon><component :is="icon" /></el-icon>
      </div>
      <div>
        <div class="agri-page-header__eyebrow">{{ eyebrow }}</div>
        <h1>{{ title }}</h1>
        <p>{{ description }}</p>
      </div>
    </div>
    <div class="agri-page-header__actions">
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  eyebrow: { type: String, default: 'SMART AGRICULTURE' },
  icon: { type: String, default: 'DataAnalysis' }
})
</script>

<style lang="scss" scoped>
.agri-page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 18px;
  padding: 22px 24px;
  border: 1px solid rgba(55, 174, 226, 0.28);
  border-radius: 8px;
  background:
    linear-gradient(90deg, rgba(6, 29, 47, 0.96), rgba(5, 24, 40, 0.94)),
    #061323;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02), 0 12px 28px rgba(0, 0, 0, 0.2);
}

.agri-page-header__main {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.agri-page-header__icon {
  display: grid;
  flex: 0 0 52px;
  width: 52px;
  height: 52px;
  place-items: center;
  border: 1px solid rgba(55, 174, 226, 0.34);
  border-radius: 8px;
  color: #eefaff;
  background: linear-gradient(145deg, rgba(8, 73, 112, 0.92), rgba(6, 42, 68, 0.92));
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.24);

  .el-icon { font-size: 26px; }
}

.agri-page-header__eyebrow {
  margin-bottom: 4px;
  color: #68dfff;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
}

h1 {
  margin: 0;
  color: #f4fbff;
  font-size: 24px;
  font-weight: 800;
  text-shadow: 0 0 12px rgba(94, 223, 255, 0.18);
}

p {
  margin: 7px 0 0;
  max-width: 780px;
  color: #c8e3ee;
  font-size: 14px;
  line-height: 1.7;
}

.agri-page-header__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 900px) {
  .agri-page-header { align-items: flex-start; flex-direction: column; }
  .agri-page-header__actions { justify-content: flex-start; width: 100%; }
}
</style>
