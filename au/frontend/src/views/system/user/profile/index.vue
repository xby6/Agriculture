<template>
  <div class="profile-page" v-loading="loading">
    <section class="profile-layout">
      <!-- 左侧个人档案 -->
      <aside class="profile-card profile-summary-card">
        <div class="card-heading">
          <div>
            <span class="heading-eyebrow">PERSONAL PROFILE</span>
            <h2>个人档案</h2>
          </div>
          <span class="account-status">
            <i></i>
            账号正常
          </span>
        </div>

        <div class="profile-identity">
          <div class="avatar-shell">
            <userAvatar />
          </div>

          <div class="identity-copy">
            <h3>{{ state.user.nickName || state.user.userName || '平台用户' }}</h3>
            <p>{{ state.roleGroup || '暂无角色信息' }}</p>
          </div>

          <span class="identity-badge">
            {{ state.user.dept?.deptName || '农业平台' }}
          </span>
        </div>

        <div class="profile-divider"></div>

        <ul class="profile-info-list">
          <li>
            <span class="info-icon">
              <svg-icon icon-class="user" />
            </span>
            <div class="info-copy">
              <small>用户名称</small>
              <strong>{{ state.user.userName || '--' }}</strong>
            </div>
          </li>

          <li>
            <span class="info-icon">
              <svg-icon icon-class="phone" />
            </span>
            <div class="info-copy">
              <small>手机号码</small>
              <strong>{{ state.user.phonenumber || '--' }}</strong>
            </div>
          </li>

          <li>
            <span class="info-icon">
              <svg-icon icon-class="email" />
            </span>
            <div class="info-copy">
              <small>用户邮箱</small>
              <strong>{{ state.user.email || '--' }}</strong>
            </div>
          </li>

          <li>
            <span class="info-icon">
              <svg-icon icon-class="tree" />
            </span>
            <div class="info-copy">
              <small>所属基地组织</small>
              <strong>
                {{
                  state.user.dept
                    ? `${state.user.dept.deptName}${state.postGroup ? ` / ${state.postGroup}` : ''}`
                    : '--'
                }}
              </strong>
            </div>
          </li>

          <li>
            <span class="info-icon">
              <svg-icon icon-class="peoples" />
            </span>
            <div class="info-copy">
              <small>所属角色</small>
              <strong>{{ state.roleGroup || '--' }}</strong>
            </div>
          </li>

          <li>
            <span class="info-icon">
              <svg-icon icon-class="date" />
            </span>
            <div class="info-copy">
              <small>创建日期</small>
              <strong>{{ formatCreateTime(state.user.createTime) }}</strong>
            </div>
          </li>
        </ul>
      </aside>

      <!-- 右侧资料编辑 -->
      <section class="profile-card profile-detail-card">
        <div class="card-heading detail-heading">
          <div>
            <span class="heading-eyebrow">ACCOUNT SETTINGS</span>
            <h2>账户资料设置</h2>
          </div>

          <div class="security-tip">
            <span class="security-icon">✓</span>
            <div>
              <strong>资料安全</strong>
              <small>请定期检查联系方式与登录密码</small>
            </div>
          </div>
        </div>

        <el-tabs v-model="activeTab" class="profile-tabs">
          <el-tab-pane name="userinfo">
            <template #label>
              <span class="tab-label">
                <svg-icon icon-class="edit" />
                基本资料
              </span>
            </template>

            <div class="tab-content">
              <div class="tab-intro">
                <h3>基本资料</h3>
                <p>维护用户昵称、手机号码、邮箱和性别等基础信息。</p>
              </div>
              <userInfo :user="state.user" />
            </div>
          </el-tab-pane>

          <el-tab-pane name="resetPwd">
            <template #label>
              <span class="tab-label">
                <svg-icon icon-class="lock" />
                修改密码
              </span>
            </template>

            <div class="tab-content">
              <div class="tab-intro">
                <h3>修改密码</h3>
                <p>建议使用包含字母、数字和特殊字符的高强度密码。</p>
              </div>
              <resetPwd />
            </div>
          </el-tab-pane>
        </el-tabs>
      </section>
    </section>
  </div>
</template>

<script setup name="Profile">
import userAvatar from './userAvatar'
import userInfo from './userInfo'
import resetPwd from './resetPwd'
import { getUserProfile } from '@/api/system/user'

const activeTab = ref('userinfo')
const loading = ref(false)

const state = reactive({
  user: {},
  roleGroup: '',
  postGroup: ''
})

function getUser() {
  loading.value = true

  getUserProfile()
    .then(response => {
      state.user = response.data || {}
      state.roleGroup = response.roleGroup || ''
      state.postGroup = response.postGroup || ''
    })
    .finally(() => {
      loading.value = false
    })
}

function formatCreateTime(value) {
  if (!value) return '--'
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return String(value)
  }

  const pad = item => String(item).padStart(2, '0')

  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

getUser()
</script>

<style lang="scss" scoped>
.profile-page {
  min-height: calc(100vh - 150px);
  padding: 20px 18px 30px;
  color: #1f3b2a;
}

.profile-layout {
  display: grid;
  grid-template-columns: minmax(300px, 350px) minmax(0, 1fr);
  align-items: start;
  gap: 18px;
  width: min(100%, 1680px);
  margin: 0 auto;
}

.profile-card {
  overflow: hidden;
  border: 1px solid #dce8df;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.97);
  box-shadow:
    0 12px 34px rgba(39, 77, 49, 0.075),
    0 1px 2px rgba(39, 77, 49, 0.035);
}

.card-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 74px;
  padding: 17px 20px;
  border-bottom: 1px solid #e5ede7;
  background:
    linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.98),
      rgba(248, 251, 248, 0.98)
    );
}

.heading-eyebrow {
  display: block;
  color: #47885a;
  font-size: 9px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 1.25px;
}

.card-heading h2 {
  margin: 7px 0 0;
  color: #193b26;
  font-size: 18px;
  line-height: 1.2;
  font-weight: 780;
}

.account-status {
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 7px;
  padding: 6px 9px;
  color: #36794a;
  border: 1px solid #cbe0d0;
  border-radius: 999px;
  background: #edf7ef;
  font-size: 10px;
  font-weight: 750;
}

.account-status i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4da368;
  box-shadow: 0 0 0 3px rgba(77, 163, 104, 0.11);
}

/* =========================================================
   左侧档案卡
========================================================= */
.profile-summary-card {
  position: sticky;
  top: 18px;
}

.profile-identity {
  display: flex;
  padding: 25px 20px 20px;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.avatar-shell {
  position: relative;
  display: grid;
  width: 112px;
  height: 112px;
  place-items: center;
  overflow: hidden;
  border: 5px solid #f3f8f4;
  border-radius: 50%;
  background: #edf6ef;
  box-shadow:
    0 0 0 1px #ccdfd1,
    0 10px 24px rgba(45, 97, 61, 0.12);
}

.avatar-shell::after {
  position: absolute;
  right: 6px;
  bottom: 8px;
  width: 14px;
  height: 14px;
  border: 3px solid #ffffff;
  border-radius: 50%;
  content: "";
  background: #4ca366;
}

.avatar-shell :deep(.user-info-head) {
  width: 100%;
  height: 100%;
  margin: 0;
}

.avatar-shell :deep(.user-avatar),
.avatar-shell :deep(img) {
  width: 100% !important;
  height: 100% !important;
  border-radius: 50% !important;
  object-fit: cover !important;
}

.avatar-shell :deep(.el-avatar) {
  width: 100% !important;
  height: 100% !important;
}

.identity-copy {
  margin-top: 16px;
}

.identity-copy h3 {
  margin: 0;
  color: #193b26;
  font-size: 20px;
  line-height: 1.25;
  font-weight: 800;
}

.identity-copy p {
  margin: 6px 0 0;
  color: #718478;
  font-size: 12px;
  line-height: 1.4;
}

.identity-badge {
  max-width: 100%;
  margin-top: 13px;
  padding: 6px 10px;
  overflow: hidden;
  color: #3c7650;
  border: 1px solid #d2e3d6;
  border-radius: 8px;
  background: #f1f8f2;
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.profile-divider {
  height: 1px;
  margin: 0 20px;
  background: #e6ede8;
}

.profile-info-list {
  margin: 0;
  padding: 12px 16px 18px;
  list-style: none;
}

.profile-info-list li {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  align-items: center;
  min-height: 61px;
  gap: 11px;
  padding: 9px 8px;
  border-bottom: 1px solid #edf2ee;
}

.profile-info-list li:last-child {
  border-bottom: 0;
}

.info-icon {
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  color: #4b8a5c;
  border: 1px solid #d3e3d7;
  border-radius: 10px;
  background: #f0f7f1;
  font-size: 15px;
}

.info-copy {
  min-width: 0;
}

.info-copy small,
.info-copy strong {
  display: block;
}

.info-copy small {
  color: #87958b;
  font-size: 9px;
  line-height: 1.2;
  font-weight: 650;
}

.info-copy strong {
  margin-top: 5px;
  overflow: hidden;
  color: #2e4c39;
  font-size: 12px;
  line-height: 1.4;
  font-weight: 700;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* =========================================================
   右侧资料卡
========================================================= */
.profile-detail-card {
  min-height: 520px;
}

.detail-heading {
  min-height: 78px;
}

.security-tip {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 9px;
  padding: 8px 11px;
  border: 1px solid #d4e4d8;
  border-radius: 10px;
  background: #f3f8f4;
}

.security-icon {
  display: grid;
  width: 27px;
  height: 27px;
  place-items: center;
  color: #ffffff;
  border-radius: 8px;
  background: #4c9861;
  font-size: 12px;
  font-weight: 800;
}

.security-tip strong,
.security-tip small {
  display: block;
  white-space: nowrap;
}

.security-tip strong {
  color: #326945;
  font-size: 10px;
  line-height: 1.2;
  font-weight: 750;
}

.security-tip small {
  margin-top: 3px;
  color: #819085;
  font-size: 8px;
}

.profile-tabs {
  padding: 0 22px 24px;
}

.profile-tabs :deep(.el-tabs__header) {
  margin: 0;
}

.profile-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background: #e3ebe5;
}

.profile-tabs :deep(.el-tabs__item) {
  height: 54px;
  padding: 0 20px;
  color: #728579;
  font-size: 12px;
  font-weight: 650;
}

.profile-tabs :deep(.el-tabs__item:hover) {
  color: #367c4c;
}

.profile-tabs :deep(.el-tabs__item.is-active) {
  color: #2f7446;
  font-weight: 800;
}

.profile-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 3px 3px 0 0;
  background: #478f5b;
}

.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.tab-content {
  padding: 22px 4px 6px;
}

.tab-intro {
  margin-bottom: 22px;
  padding: 15px 17px;
  border: 1px solid #dfe9e2;
  border-radius: 11px;
  background: #f7faf7;
}

.tab-intro h3 {
  margin: 0;
  color: #224631;
  font-size: 14px;
  line-height: 1.3;
  font-weight: 780;
}

.tab-intro p {
  margin: 6px 0 0;
  color: #7d8e82;
  font-size: 10px;
  line-height: 1.5;
}

/* 子组件表单样式统一 */
.profile-tabs :deep(.el-form) {
  max-width: 920px;
}

.profile-tabs :deep(.el-form-item) {
  margin-bottom: 21px;
}

.profile-tabs :deep(.el-form-item__label) {
  color: #476252 !important;
  font-size: 12px;
  font-weight: 700;
}

.profile-tabs :deep(.el-input__wrapper),
.profile-tabs :deep(.el-select__wrapper) {
  min-height: 42px;
  border: 1px solid #d7e3da;
  border-radius: 9px;
  background: #ffffff;
  box-shadow: none !important;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.profile-tabs :deep(.el-input__wrapper:hover),
.profile-tabs :deep(.el-select__wrapper:hover) {
  border-color: #accbb4;
}

.profile-tabs :deep(.el-input__wrapper.is-focus),
.profile-tabs :deep(.el-select__wrapper.is-focused) {
  border-color: #559968;
  box-shadow: 0 0 0 3px rgba(85, 153, 104, 0.1) !important;
}

.profile-tabs :deep(.el-input__inner),
.profile-tabs :deep(.el-select__selected-item),
.profile-tabs :deep(.el-radio__label) {
  color: #385642;
  font-size: 12px;
}

.profile-tabs :deep(.el-radio__input.is-checked .el-radio__inner) {
  border-color: #478f5b;
  background: #478f5b;
}

.profile-tabs :deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #367c4c;
}

.profile-tabs :deep(.el-button) {
  min-width: 76px;
  height: 38px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
}

.profile-tabs :deep(.el-button--primary) {
  border-color: #3f8d57;
  background: linear-gradient(180deg, #4e9b64, #397f4f);
  box-shadow: 0 7px 16px rgba(57, 127, 79, 0.16);
}

.profile-tabs :deep(.el-button--primary:hover) {
  border-color: #347747;
  background: linear-gradient(180deg, #58a66d, #347747);
}

.profile-tabs :deep(.el-button:not(.el-button--primary)) {
  color: #576d5e;
  border-color: #d4e0d7;
  background: #f7faf7;
}

.profile-tabs :deep(.el-button--danger),
.profile-tabs :deep(.el-button--warning) {
  color: #ffffff;
  border-color: #d2675f;
  background: #d2675f;
  box-shadow: none;
}

/* =========================================================
   响应式
========================================================= */
@media (max-width: 1050px) {
  .profile-layout {
    grid-template-columns: 300px minmax(0, 1fr);
  }

  .security-tip small {
    display: none;
  }
}

@media (max-width: 820px) {
  .profile-page {
    padding: 14px 12px 24px;
  }

  .profile-layout {
    grid-template-columns: 1fr;
  }

  .profile-summary-card {
    position: static;
  }

  .profile-info-list {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0 12px;
  }

  .profile-info-list li {
    min-width: 0;
  }
}

@media (max-width: 560px) {
  .profile-info-list {
    grid-template-columns: 1fr;
  }

  .card-heading {
    padding-right: 14px;
    padding-left: 14px;
  }

  .security-tip {
    display: none;
  }

  .profile-tabs {
    padding-right: 14px;
    padding-left: 14px;
  }

  .profile-tabs :deep(.el-tabs__item) {
    padding: 0 12px;
  }
}
</style>
