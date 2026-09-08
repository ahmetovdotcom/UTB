import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'Расписание okak.asia',
        short_name: 'okak.asia',
        description: 'Удобное расписание занятий университета',
        theme_color: '#ffffff',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/',
        icons: [
          {
            src: '/logo-192-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/logo-512-512.png',
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: '/logo-512-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      },
      workbox: {
        // Кэшируем статику (JS, CSS, HTML, картинки)
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        // Кэшируем ответы API, чтобы расписание было доступно оффлайн
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/okak\.asia\/api\/v1\/.*/i,
            handler: 'NetworkFirst', // Сначала пробует сеть, при отсутствии сети берёт из кэша
            options: {
              cacheName: 'api-schedule-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24 * 7 // Кэш на 7 дней
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          }
        ]
      }
    })
  ]
})