import auth from '@/plugins/auth'
import router, { constantRoutes, dynamicRoutes } from '@/router'
import { getRouters } from '@/api/menu'
import Layout from '@/layout/index'
import ParentView from '@/components/ParentView'
import InnerLink from '@/layout/components/InnerLink'

const modules = import.meta.glob('./../../views/**/*.vue')

const usePermissionStore = defineStore('permission', {
  state: () => ({
    routes: [],
    addRoutes: [],
    defaultRoutes: [],
    topbarRouters: [],
    sidebarRouters: []
  }),
  actions: {
    setRoutes(routes) {
      this.addRoutes = routes
      this.routes = constantRoutes.concat(routes)
    },
    setDefaultRoutes(routes) {
      this.defaultRoutes = constantRoutes.concat(routes)
    },
    setTopbarRoutes(routes) {
      this.topbarRouters = routes
    },
    setSidebarRouters(routes) {
      this.sidebarRouters = routes
    },
    async generateRoutes() {
      // 不再使用只 resolve、不 reject 的手写 Promise，避免 getRouters 报错后永久 pending。
      const res = await getRouters()
      if (!res || !Array.isArray(res.data)) {
        throw new Error('后端 /getRouters 返回格式不正确')
      }

      const sdata = JSON.parse(JSON.stringify(res.data))
      const rdata = JSON.parse(JSON.stringify(res.data))
      const defaultData = JSON.parse(JSON.stringify(res.data))
      const sidebarRoutes = filterAsyncRouter(sdata)
      const rewriteRoutes = filterAsyncRouter(rdata, false, true)
      const defaultRoutes = filterAsyncRouter(defaultData)
      const asyncRoutes = filterDynamicRoutes(dynamicRoutes)

      asyncRoutes.forEach(route => router.addRoute(route))
      this.setRoutes(rewriteRoutes)
      this.setSidebarRouters(constantRoutes.concat(sidebarRoutes))
      this.setDefaultRoutes(sidebarRoutes)
      this.setTopbarRoutes(defaultRoutes)
      return rewriteRoutes
    }
  }
})

function filterAsyncRouter(asyncRouterMap, lastRouter = false, type = false) {
  return asyncRouterMap.filter(route => {
    if (type && route.children) route.children = filterChildren(route.children)

    if (route.component) {
      if (route.component === 'Layout') {
        route.component = Layout
      } else if (route.component === 'ParentView') {
        route.component = ParentView
      } else if (route.component === 'InnerLink') {
        route.component = InnerLink
      } else {
        const component = loadView(route.component)
        if (!component) {
          throw new Error(`菜单组件不存在：src/views/${route.component}.vue`)
        }
        route.component = component
      }
    }

    if (route.children && route.children.length) {
      route.children = filterAsyncRouter(route.children, route, type)
    } else {
      delete route.children
      delete route.redirect
    }
    return true
  })
}

function filterChildren(childrenMap, lastRouter = false) {
  let children = []
  childrenMap.forEach(el => {
    if (el.children && el.children.length && el.component === 'ParentView' && !lastRouter) {
      el.children.forEach(c => {
        c.path = el.path + '/' + c.path
        if (c.children && c.children.length) {
          children = children.concat(filterChildren(c.children, c))
        } else {
          children.push(c)
        }
      })
      return
    }

    if (lastRouter) {
      el.path = lastRouter.path + '/' + el.path
      if (el.children && el.children.length) {
        children = children.concat(filterChildren(el.children, el))
        return
      }
    }
    children = children.concat(el)
  })
  return children
}

export function filterDynamicRoutes(routes) {
  const res = []
  routes.forEach(route => {
    if (route.permissions) {
      if (auth.hasPermiOr(route.permissions)) res.push(route)
    } else if (route.roles) {
      if (auth.hasRoleOr(route.roles)) res.push(route)
    }
  })
  return res
}

export const loadView = (view) => {
  const normalizedView = String(view || "")
    .replace(/\\/g, "/")
    .replace(/^\/+/, "")
    .replace(/^src\/views\//, "")
    .replace(/\.vue$/, "");

  for (const path in modules) {
    const normalizedPath = path
      .split("views/")[1]
      .replace(/\.vue$/, "");

    if (normalizedPath === normalizedView) {
      return modules[path];
    }
  }

  console.error(
    `未找到菜单组件：src/views/${normalizedView}.vue`
  );

  console.error(
    "当前可以加载的组件：",
    Object.keys(modules).map((path) =>
      path.split("views/")[1].replace(/\.vue$/, "")
    )
  );

  // 暂时返回404页面，避免单个错误菜单阻塞整个系统登录
  return () => import("@/views/error/404.vue");
};

export default usePermissionStore
