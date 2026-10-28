<template>
  <div class="login-page">
    
    <div class="scene-grid"></div>
    <div class="scene-glow scene-glow-one"></div>
    <div class="scene-glow scene-glow-two"></div>

    <main class="login-shell">

      <el-form
        ref="loginRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-card"
      >
        <span class="card-top-line"></span>

        <header class="login-header">
          <div class="brand-mark">
  <img
    src="/a.png"
    class="brand-logo-img"
    alt="水稻病害监测平台"
  />
</div>
          <div class="login-title-group">
            <span class="login-eyebrow">WELCOME BACK</span>
            <h2>农业智能管理中心</h2>
          </div>
        </header>

        <div class="login-divider">
          <span></span>
          <span></span>
        </div>

        <div class="form-label"></div>
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            type="text"
            size="large"
            autocomplete="off"
            placeholder="请输入平台账号"
            class="login-input"
          >
            <template #prefix>
              <svg-icon icon-class="user" class="input-icon" />
            </template>
          </el-input>
        </el-form-item>

        <div class="form-label"></div>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            size="large"
            autocomplete="off"
            placeholder="请输入登录密码"
            show-password
            class="login-input"
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <svg-icon icon-class="password" class="input-icon" />
            </template>
          </el-input>
        </el-form-item>

        <template v-if="captchaEnabled">
          <div class="form-label">验证码</div>
          <el-form-item prop="code">
            <div class="captcha-wrap">
              <el-input
                v-model="loginForm.code"
                size="large"
                autocomplete="off"
                placeholder="请输入验证码"
                class="login-input captcha-input"
                @keyup.enter="handleLogin"
              >
                <template #prefix>
                  <svg-icon icon-class="validCode" class="input-icon" />
                </template>
              </el-input>

              <button
                class="captcha-image-wrap"
                type="button"
                title="点击刷新验证码"
                @click="getCode"
              >
                <img :src="codeUrl" class="login-code-img" alt="验证码" />
                <span>点击刷新</span>
              </button>
            </div>
          </el-form-item>
        </template>

        <div class="login-options">
          <el-checkbox v-model="loginForm.rememberMe">
            记住密码
          </el-checkbox>

          <router-link
            v-if="register"
            class="register-link"
            :to="'/register'"
          >
            立即注册
          </router-link>
        </div>

        <el-form-item class="login-button-item">
          <el-button
            :loading="loading"
            size="large"
            type="primary"
            class="login-button"
            @click.prevent="handleLogin"
          >
            <span v-if="!loading">登录平台</span>
            <span v-else>正在验证...</span>
          </el-button>
        </el-form-item>

        <div class="security-note">
          <span class="security-icon">✓</span>
          <p>账号信息采用加密传输，请妥善保管登录凭证</p>
        </div>

        <div class="card-corner card-corner-left"></div>
        <div class="card-corner card-corner-right"></div>
      </el-form>
    </main>

    <footer class="login-footer">
      <span>水稻病害智能监测与预测平台</span>
      <i></i>
      <span>农业数据与算法一体化管理</span>
    </footer>
  </div>
</template>

<script setup>
import { ElMessage } from "element-plus";
import { getCodeImg } from "@/api/login";
import Cookies from "js-cookie";
import { encrypt, decrypt } from "@/utils/jsencrypt";
import useUserStore from "@/store/modules/user";

const userStore = useUserStore();
const route = useRoute();
const router = useRouter();
const { proxy } = getCurrentInstance();

const loginForm = ref({
  username: "",
  password: "",
  rememberMe: false,
  code: "",
  uuid: ""
});

const loginRules = {
  username: [{ required: true, trigger: "blur", message: "请输入您的账号" }],
  password: [{ required: true, trigger: "blur", message: "请输入您的密码" }],
  code: [{ required: true, trigger: "change", message: "请输入验证码" }]
};

const codeUrl = ref("");
const loading = ref(false);
const captchaEnabled = ref(true);
const register = ref(false);
const redirect = ref(undefined);

watch(
  route,
  (newRoute) => {
    redirect.value = newRoute.query && newRoute.query.redirect;
  },
  { immediate: true }
);

async function handleLogin() {
  if (loading.value) return;

  const valid = await new Promise((resolve) => {
    proxy.$refs.loginRef.validate((result) => resolve(result));
  });

  if (!valid) return;

  loading.value = true;

  try {
    if (loginForm.value.rememberMe) {
      Cookies.set("username", loginForm.value.username, { expires: 30 });
      Cookies.set("password", encrypt(loginForm.value.password), { expires: 30 });
      Cookies.set("rememberMe", "true", { expires: 30 });
    } else {
      Cookies.remove("username");
      Cookies.remove("password");
      Cookies.remove("rememberMe");
    }

    await userStore.login(loginForm.value);

    const query = route.query || {};
    const otherQueryParams = Object.keys(query).reduce((result, key) => {
      if (key !== "redirect") result[key] = query[key];
      return result;
    }, {});

    const targetPath = redirect.value || "/screen";

    await Promise.race([
      router.replace({
        path: targetPath,
        query: otherQueryParams
      }),
      new Promise((_, reject) => {
        setTimeout(() => {
          reject(
            new Error(
              "登录成功，但系统初始化超时，请检查 /getInfo、/getRouters 或菜单组件路径"
            )
          );
        }, 15000);
      })
    ]);
  } catch (error) {
    console.error("登录或系统初始化失败：", error);

    ElMessage.error(
      error?.message ||
        error?.response?.data?.msg ||
        "登录后系统初始化失败"
    );

    if (captchaEnabled.value) getCode();
  } finally {
    loading.value = false;
  }
}

function getCode() {
  getCodeImg().then((res) => {
    captchaEnabled.value =
      res.captchaEnabled === undefined ? true : res.captchaEnabled;
    register.value =
      res.registerEnabled === undefined ? false : res.registerEnabled;

    if (captchaEnabled.value) {
      codeUrl.value = "data:image/gif;base64," + res.img;
      loginForm.value.uuid = res.uuid;
    }
  });
}

function getCookie() {
  const username = Cookies.get("username");
  const password = Cookies.get("password");
  const rememberMe = Cookies.get("rememberMe");

  loginForm.value = {
    username: username === undefined ? loginForm.value.username : username,
    password:
      password === undefined
        ? loginForm.value.password
        : decrypt(password),
    rememberMe:
      rememberMe === undefined ? false : Boolean(rememberMe),
    code: "",
    uuid: ""
  };
}

getCode();
getCookie();
</script>

<style lang="scss" scoped>
.login-page {
  --primary: #39d56f;
  --primary-deep: #158342;
  --text-main: #f2fbf8;
  --text-secondary: #b7d2cc;
  --text-muted: #789a94;

  position: relative;
  display: flex;
  width: 100%;
  min-height: 100vh;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  color: var(--text-main);
  background: url("@/assets/images/bgn.png") center center / cover no-repeat fixed;
}


.scene-overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(
      90deg,
      rgba(1, 19, 24, 0.78) 0%,
      rgba(2, 24, 29, 0.54) 37%,
      rgba(2, 20, 28, 0.34) 63%,
      rgba(2, 15, 23, 0.72) 100%
    ),
    linear-gradient(
      180deg,
      rgba(2, 18, 23, 0.12),
      rgba(2, 19, 20, 0.5)
    );
}

.scene-grid {
  position: absolute;
  inset: 0;
  opacity: 0.13;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(112, 220, 201, 0.12) 1px, transparent 1px),
    linear-gradient(90deg, rgba(112, 220, 201, 0.12) 1px, transparent 1px);
  background-size: 64px 64px;
  mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.7), transparent 74%);
}

.scene-glow {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.scene-glow-one {
  top: -180px;
  left: 28%;
  width: 460px;
  height: 460px;
  background: radial-gradient(circle, rgba(47, 211, 170, 0.14), transparent 68%);
}

.scene-glow-two {
  right: -160px;
  bottom: -220px;
  width: 520px;
  height: 520px;
  background: radial-gradient(circle, rgba(52, 203, 103, 0.15), transparent 70%);
}

.login-shell {
  position: relative;
  z-index: 2;
  display: flex;
  width: min(470px, calc(100vw - 40px));
  align-items: center;
  justify-content: center;
  padding: 54px 0 78px;
}


.login-card {
  position: relative;
  width: 100%;
  padding: 34px 36px 27px;
  overflow: hidden;

  /* 偏蓝灰的玻璃边框，与天空背景更协调 */
  border: 1px solid rgba(85, 220, 132, 0.36);
  border-radius: 20px;

  /* 主体由墨绿色改成深海蓝灰色 */
  background:
    linear-gradient(
      145deg,
      rgba(7, 48, 31, 0.90) 0%,
      rgba(5, 38, 25, 0.93) 50%,
      rgba(3, 27, 19, 0.95) 100%
    );

  box-shadow:
    0 30px 80px rgba(1, 18, 30, 0.36),
    0 0 30px rgba(63, 213, 113, 0.11),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);

  backdrop-filter: blur(22px) saturate(120%);
  -webkit-backdrop-filter: blur(22px) saturate(120%);
}

.login-card::before {
  position: absolute;
  top: -120px;
  right: -105px;
  width: 260px;
  height: 260px;
  border-radius: 50%;
  content: "";
  pointer-events: none;

  background:
    radial-gradient(
      circle,
      rgba(62, 215, 113, 0.18),
      transparent 68%
    );
}

.card-top-line {
  position: absolute;
  top: 0;
  right: 48px;
  left: 48px;
  height: 2px;
  border-radius: 0 0 4px 4px;

  background:
    linear-gradient(
      90deg,
      transparent,
      rgba(83, 225, 130, 0.9),
      rgba(70, 215, 111, 0.74),
      transparent
    );
}

.login-header {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 15px;
}

.brand-mark {
  position: relative;
  display: grid;
  width: 62px;
  height: 62px;
  flex: 0 0 62px;
  place-items: center;
  overflow: hidden;
  border: 1px solid rgba(106, 231, 194, 0.34);
  border-radius: 18px;
  color: #ecfff8;
  background:
    radial-gradient(
      circle at 28% 22%,
      rgba(255, 255, 255, 0.2),
      transparent 35%
    ),
    linear-gradient(
      145deg,
      rgba(48, 201, 145, 0.96),
      rgba(17, 115, 88, 0.98)
    );
  box-shadow:
    0 14px 30px rgba(13, 112, 79, 0.34),
    inset 0 1px 0 rgba(255, 255, 255, 0.22);
}

.brand-mark::before {
  position: absolute;
  inset: 7px;
  border: 1px solid rgba(235, 255, 248, 0.14);
  border-radius: 13px;
  content: "";
}

.brand-mark::after {
  position: absolute;
  right: -12px;
  bottom: -18px;
  width: 48px;
  height: 48px;
  border: 1px solid rgba(236, 255, 248, 0.11);
  border-radius: 50%;
  content: "";
}
.brand-logo-img {
  position: relative;
  z-index: 2;
  display: block;
  width: 42px;
  height: 42px;
  object-fit: contain;
  user-select: none;
}

.login-eyebrow {
  display: block;
  margin-bottom: 4px;
  color: #58dcb4;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 1.5px;
}

.login-title-group h2 {
  margin: 0;
  color: #f5fffb;
  font-size: 24px;
}

.login-title-group p {
  margin: 5px 0 0;
  color: #87aaa3;
  font-size: 10px;
}

.login-divider {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 10px;
  margin: 25px 0 20px;
}

.login-divider span {
  height: 1px;
  background: rgba(127, 192, 181, 0.16);
}

.login-divider em {
  color: #6f928b;
  font-size: 9px;
  font-style: normal;
  letter-spacing: 1px;
}

.form-label {
  margin: 0 0 7px 2px;
  color: #bad4ce;
  font-size: 11px;
  font-weight: 650;
}

.login-card :deep(.el-form-item) {
  margin-bottom: 17px;
}

.login-card :deep(.el-form-item__error) {
  padding-top: 4px;
  color: #ff9b9b;
  font-size: 10px;
}

.login-input :deep(.el-input__wrapper) {
  min-height: 46px;
  padding: 0 14px;
  border: 1px solid rgba(119, 182, 174, 0.16);
  border-radius: 11px;
  background: rgba(2, 17, 24, 0.64);
  box-shadow: none;
  transition: 0.2s ease;
}

.login-input :deep(.el-input__wrapper:hover) {
  border-color: rgba(99, 213, 185, 0.29);
  background: rgba(3, 24, 30, 0.76);
}

.login-input :deep(.el-input__wrapper.is-focus) {
  border-color: rgba(80, 223, 181, 0.58);
  background: rgba(3, 26, 31, 0.85);
  box-shadow: 0 0 0 3px rgba(66, 211, 156, 0.08);
}

.login-input :deep(.el-input__inner) {
  color: #effbf8;
  font-size: 13px;
}

.login-input :deep(.el-input__inner::placeholder) {
  color: #597a74;
}

.input-icon {
  width: 15px;
  height: 15px;
  margin-right: 3px;
}

.captcha-wrap {
  display: grid;
  width: 100%;
  grid-template-columns: minmax(0, 1fr) 122px;
  gap: 10px;
}

.captcha-image-wrap {
  position: relative;
  height: 46px;
  padding: 0;
  overflow: hidden;
  border: 1px solid rgba(119, 182, 174, 0.18);
  border-radius: 11px;
  cursor: pointer;
  background: rgba(234, 245, 241, 0.94);
}

.login-code-img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: fill;
}

.captcha-image-wrap span {
  position: absolute;
  right: 5px;
  bottom: 3px;
  padding: 2px 4px;
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.78);
  background: rgba(2, 17, 24, 0.64);
  font-size: 7px;
}

.login-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: -2px 1px 19px;
}

.login-card :deep(.el-checkbox__label) {
  color: #9cbab3;
  font-size: 11px;
}

.login-card :deep(.el-checkbox__inner) {
  border-color: rgba(111, 180, 167, 0.35);
  background: rgba(2, 17, 24, 0.55);
}

.login-card :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  border-color: #34bc89;
  background: #34bc89;
}

.register-link {
  color: #5adab2;
  font-size: 11px;
  text-decoration: none;
}

.login-button-item {
  margin-bottom: 15px !important;
}

.login-button {
  width: 100%;
  height: 47px;

  border: 1px solid rgba(104, 232, 146, 0.36);
  border-radius: 11px;

  color: #f7fdff;

  background:
    linear-gradient(
      135deg,
      #05f07a 0%,
      #03ba2b 52%,
      #038607 100%
    );

  box-shadow:
    0 12px 28px rgba(13, 132, 65, 0.31),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);

  font-size: 14px;
  font-weight: 750;
  letter-spacing: 4px;

  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    filter 0.2s ease;
}

.login-button:hover {
  transform: translateY(-1px);
  filter: brightness(1.08);

  box-shadow:
    0 16px 34px rgba(13, 132, 65, 0.40),
    inset 0 1px 0 rgba(255, 255, 255, 0.24);
}

.login-button:hover {
  transform: translateY(-1px);
  filter: brightness(1.07);
}

.security-note {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
}

.security-icon {
  display: grid;
  width: 15px;
  height: 15px;
  place-items: center;
  border: 1px solid rgba(78, 208, 164, 0.26);
  border-radius: 50%;
  color: #62dcb3;
  font-size: 8px;
}

.security-note p {
  margin: 0;
  color: #688a84;
  font-size: 9px;
}

.card-corner {
  position: absolute;
  bottom: 12px;
  width: 19px;
  height: 19px;
}

.card-corner-left {
  left: 12px;
  border-bottom: 1px solid rgba(81, 220, 181, 0.36);
  border-left: 1px solid rgba(81, 220, 181, 0.36);
}

.card-corner-right {
  right: 12px;
  border-right: 1px solid rgba(81, 220, 181, 0.36);
  border-bottom: 1px solid rgba(81, 220, 181, 0.36);
}

.login-footer {
  position: fixed;
  z-index: 3;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  height: 44px;
  align-items: center;
  justify-content: center;
  gap: 11px;
  color: rgba(208, 230, 224, 0.62);
  background: linear-gradient(180deg, transparent, rgba(2, 16, 20, 0.46));
  font-size: 10px;
  letter-spacing: 1px;
}

.login-footer i {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: rgba(87, 213, 177, 0.7);
}

@media (max-width: 820px) {
  .login-page {
    align-items: flex-start;
    overflow-y: auto;
  }

  .login-shell {
    width: min(460px, calc(100vw - 30px));
    padding: 44px 0 76px;
  }

  .login-card {
    width: 100%;
  }

  .scene-overlay {
    background:
      linear-gradient(
        180deg,
        rgba(2, 20, 25, 0.52),
        rgba(1, 15, 21, 0.76)
      );
  }
}

@media (max-width: 520px) {
  .login-shell {
    width: calc(100vw - 22px);
    padding-top: 24px;
  }

  .login-card {
    padding: 27px 21px 23px;
    border-radius: 17px;
  }

  .brand-mark {
    width: 56px;
    height: 56px;
    flex-basis: 56px;
    border-radius: 16px;
  }

  .brand-logo {
    width: 38px;
    height: 38px;
  }

  .captcha-wrap {
    grid-template-columns: minmax(0, 1fr) 108px;
  }

  .login-footer {
    height: 38px;
    gap: 7px;
    font-size: 8px;
  }
}
</style>
