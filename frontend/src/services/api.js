// src/services/api.js

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const scheduleApi = {
  /**
   * Получить список всех групп
   */
  async getGroups() {
    const response = await fetch(`${API_URL}/groups`)
    if (!response.ok) {
      throw new Error(`Ошибка загрузки групп: ${response.status}`)
    }
    return response.json()
  },

  /**
   * Получить расписание для группы по дню недели
   * @param {number|string} groupId 
   * @param {number} day 
   */
  async getSchedule(groupId, day) {
    const response = await fetch(`${API_URL}/schedules/${groupId}?day=${day}`)
    if (!response.ok) {
      throw new Error(`Ошибка загрузки расписания: ${response.status}`)
    }
    return response.json()
  }
}