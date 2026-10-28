import { login, logout, getInfo } from '@/api/login'
import { getToken, setToken, removeToken } from '@/utils/auth'
import { isHttp, isEmpty } from '@/utils/validate'
import defAva from '@/assets/images/profile.jpg'

const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken(),
    id: '',
    name: '',
    avatar: '',
    roles: [],
    permissions: []
  }),
  actions: {
    async login(userInfo) {
      const res = await login(
        userInfo.username.trim(),
        userInfo.password,
        userInfo.code,
        userInfo.uuid
      )
      if (!res?.token) throw new Error('登录接口未返回 token')
      setToken(res.token)
      this.token = res.token
    },

    async getInfo() {
      const res = await getInfo()
      if (!res?.user) throw new Error('后端 /getInfo 未返回用户信息')

      const user = res.user
      let avatar = user.avatar || ''
      if (!isHttp(avatar)) {
        avatar = isEmpty(avatar) ? defAva : import.meta.env.VITE_APP_BASE_API + avatar
      }

      if (res.roles && res.roles.length > 0) {
        this.roles = res.roles
        this.permissions = res.permissions || []
      } else {
        this.roles = ['ROLE_DEFAULT']
      }

      this.id = user.userId
      this.name = user.userName
      this.avatar = avatar
      return res
    },

    async logOut() {
      try {
        await logout(this.token)
      } finally {
        await this.resetToken()
      }
    },

    resetToken() {
      this.token = ''
      this.id = ''
      this.name = ''
      this.avatar = ''
      this.roles = []
      this.permissions = []
      removeToken()
      return Promise.resolve()
    }
  }
})

export default useUserStore
