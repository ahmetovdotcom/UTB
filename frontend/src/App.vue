<script setup>
import { ref, onMounted, watch } from 'vue'
import GroupSelector from './components/GroupSelector.vue'
import DayTabs from './components/DayTabs.vue'
import LessonCard from './components/LessonCard.vue'
import IosSetupModal from './components/IosSetupModal.vue'
import { scheduleApi } from './services/api'

const getTodayDayOfWeek = () => {
  const day = new Date().getDay()
  return day === 0 ? 7 : day
}

const groups = ref([])
const selectedGroup = ref(null)
const currentDay = ref(getTodayDayOfWeek())
const lessons = ref([])
const isLoading = ref(false)
const isModalOpen = ref(false)

onMounted(async () => {
  const savedGroupId = localStorage.getItem('user_group_id')
  await fetchGroups()

  if (savedGroupId && groups.value.length) {
    const found = groups.value.find(g => String(g.id) === String(savedGroupId))
    if (found) {
      selectedGroup.value = found
    }
  }
})

const fetchGroups = async () => {
  try {
    groups.value = await scheduleApi.getGroups()
  } catch (error) {
    console.error('Ошибка при получении списка групп:', error)
  }
}

const fetchSchedule = async () => {
  if (!selectedGroup.value) return
  isLoading.value = true

  try {
    lessons.value = await scheduleApi.getSchedule(selectedGroup.value.id, currentDay.value)
  } catch (error) {
    console.error('Ошибка при получении расписания:', error)
  } finally {
    isLoading.value = false
  }
}

const handleGroupSelect = (group) => {
  selectedGroup.value = group
  localStorage.setItem('user_group_id', group.id)
}

watch([selectedGroup, currentDay], () => {
  if (selectedGroup.value) {
    fetchSchedule()
  }
})
</script>

<template>
  <div class="app-container">
    <header class="header">
      <h1 class="logo">Расписание</h1>

      <div class="header-actions">
        <button @click="isModalOpen = true" class="ios-btn" type="button" title="Настройка iOS">
          📱 <span class="ios-btn-text">iOS</span>
        </button>

        <GroupSelector
          :groups="groups"
          :selected-group="selectedGroup"
          @select-group="handleGroupSelect"
        />
      </div>
    </header>

    <main v-if="selectedGroup" class="main-content">
      <DayTabs v-model="currentDay" />

      <div class="schedule-section">
        <div v-if="isLoading" class="state-msg">Загрузка...</div>

        <div v-else-if="lessons.length === 0" class="state-msg empty">
          🎉 Занятий нет, можно отдыхать!
        </div>

        <div v-else class="lessons-list">
          <LessonCard
            v-for="lesson in lessons"
            :key="lesson.id"
            :time="lesson.time"
            :subject="lesson.subject"
            :room="lesson.room"
          />
        </div>
      </div>
    </main>

    <div v-else class="welcome-screen">
      <p>Выберите вашу группу вверху, чтобы посмотреть расписание</p>
    </div>

    <IosSetupModal 
      :is-open="isModalOpen" 
      @close="isModalOpen = false" 
    />
  </div>
</template>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
}

body {
  background-color: #000000;
  color: #ffffff;
  display: flex;
  justify-content: center;
  min-height: 100vh;
}

#app {
  width: 100%;
  max-width: 480px;
}

.app-container {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-top: 10px;
}

.logo {
  font-size: 1.25rem;
  font-weight: 700;
  color: #ffffff;
  white-space: nowrap;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.ios-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #ffffff;
  background-color: #1c1c1e;
  border: 1px solid #2c2c2e;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  white-space: nowrap;
}

.ios-btn:hover {
  background-color: #2c2c2e;
}

/* Скрываем текст "iOS" на экранах уже 380px, оставляя только эмодзи 📱 */
@media (max-width: 380px) {
  .ios-btn-text {
    display: none;
  }
  
  .logo {
    font-size: 1.1rem;
  }
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.lessons-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.state-msg {
  text-align: center;
  color: #8e8e93;
  padding: 40px 0;
  font-size: 1.05rem;
}

.welcome-screen {
  text-align: center;
  color: #8e8e93;
  margin-top: 60px;
}
</style>