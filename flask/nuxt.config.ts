// https://nuxt.com/docs/api/configuration/nuxt-config

export default defineNuxtConfig({
  ssr: false,

  // Write the generated static site straight to flask/dist instead of the default
  // .output/public. Nitro only symlinks dist -> output.publicDir when dist doesn't already
  // exist (see @nuxt/nitro-server's symlinkDist()); pointing publicDir at dist itself means
  // `npm run generate`/`npm run build` produce a real, populated flask/dist directly -- no
  // symlink at all, so pyset/server_app.py and every build/packaging path (Dockerfile,
  // generate_distrib_package.sh/.bat) can rely on it being real files without their own
  // workarounds. Scoped to $production only: `nuxt dev`'s startup also clears whatever
  // output.publicDir points at, so applying this unconditionally means simply running
  // `npm run dev` silently wipes an already-generated flask/dist (verified: it does).
  // Dev mode keeps Nitro's default .output/public, which dev's own cleanup already targets
  // harmlessly today.
  $production: {
    nitro: {
      output: {
        publicDir: '{{ rootDir }}/dist'
      }
    }
  },

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
