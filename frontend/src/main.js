import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { registerSW } from 'virtual:vite-plugin-pwa'


registerSW({ immediate: true })
createApp(App).mount('#app')
