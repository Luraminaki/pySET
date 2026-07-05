// https://nuxt.com/docs/api/configuration/nuxt-config

export default defineNuxtConfig({
  ssr: false,

  // Works around a Nuxt/Vite regression (nuxt/nuxt#35033) where `nuxt dev`/`build` crashes with
  // "No entry found in rollupOptions.input" on ssr:false projects. Fixed upstream in nuxt/nuxt#35037
  // (targeted for 3.21.9+); remove this once that lands and gets picked up.
  experimental: {
    viteEnvironmentApi: true
  },

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
        { name: 'description', content: 'SET! game web app written in VUE 3 and Python 3.' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: 'favicon.ico' }
      ],
      bodyAttrs: { style: 'overflow-y: auto; min-height: 100vh; min-height: -webkit-fill-available;' }
    }
  },

  modules: ['@bootstrap-vue-next/nuxt', '@pinia/nuxt'],
  css: [
    'bootstrap/dist/css/bootstrap.min.css',
    '@mdi/font/css/materialdesignicons.css'
  ],

  components: true
})
