import router from './router'
import { ElMessage } from 'element-plus'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { getToken } from '@/utils/auth'
import { isHttp, isPathMatch } from '@/utils/validate'
import { isRelogin } from '@/utils/request'
import useUserStore from '@/store/modules/user'
import useSettingsStore from '@/store/modules/settings'
import usePermissionStore from '@/store/modules/permission'

NProgress.configure({ showSpinner: false })

const whiteList = ['/', '/screen', '/login', '/register']
const isWhiteList = path => whiteList.some(pattern => isPathMatch(pattern, path))

function withTimeout(promise, ms, message) {
  let timer
  const timeout = new Promise((_, reject) => {
    timer = window.setTimeout(() => reject(new Error(message)), ms)
  })
  return Promise.race([promise, timeout]).finally(() => window.clearTimeout(timer))
}

router.beforeEach(async (to, from, next) => {
  NProgress.start()
  const token = getToken()

  if (!token) {
    if (isWhiteList(to.path)) {
      next()
    } else {
      next(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
      NProgress.done()
    }
    return
  }

  to.meta.title && useSettingsStore().setTitle(to.meta.title)

  if (to.path === '/login') {
    next({ path: '/screen' })
    NProgress.done()
    return
  }

  if (isWhiteList(to.path)) {
    next()
    return
  }

  const userStore = useUserStore()
  const permissionStore = usePermissionStore()

  if (userStore.roles.length > 0) {
    next()
    return
  }

  try {
    isRelogin.show = true
    await withTimeout(userStore.getInfo(), 12000, '获取用户信息超时，请检查后端 /getInfo 接口')
    const accessRoutes = await withTimeout(
      permissionStore.generateRoutes(),
      12000,
      '加载菜单路由超时，请检查后端 /getRouters 接口和数据库菜单数据'
    )

    accessRoutes.forEach(route => {
      if (!isHttp(route.path)) router.addRoute(route)
    })

    isRelogin.show = false
    next({ ...to, replace: true })
  } catch (error) {
    isRelogin.show = false
    await userStore.resetToken()
    ElMessage.error(error?.message || '登录后初始化失败，请检查后端日志')
    next(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
    NProgress.done()
  }
})

router.afterEach(() => NProgress.done())
