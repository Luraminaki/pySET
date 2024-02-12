// https://nuxt.com/docs/api/configuration/nuxt-config

export default defineNuxtConfig({
  ssr: false,

  vite: {
    css: {
      preprocessorOptions: {
        scss: { }
      }
    },
  },

  app: {
    head: {
      title: 'pySET',
      charset: 'utf-8',
      viewport: 'width=device-width, initial-scale=1',
      htmlAttrs: {
        lang: 'en',
        style: 'overflow-y: auto; height: -webkit-fill-available;'
      },
      meta: [
        { name: 'description', content: 'pySET WebApp' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: 'favicon.ico' }
      ],
      bodyAttrs: { style: 'overflow-y: auto; min-height: 100vh; min-height: -webkit-fill-available;' }
    }
  },

  modules: ['@bootstrap-vue-next/nuxt'],
  css: [
    'bootstrap/dist/css/bootstrap.min.css',
    '@mdi/font/css/materialdesignicons.css'
  ],

  components: true
})
