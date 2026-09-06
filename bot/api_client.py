import httpx 
from config import settings


class APIClient:
    def __init__(self):
        # Единый AsyncClient с переиспользованием TCP-соединений (HTTP Keep-Alive)
        self.client = httpx.AsyncClient(
            base_url=settings.API_URL,
            headers={"Authorization": f"Bearer {settings.API_SECRET_KEY}"},
            timeout=10.0
        )

    async def get_user(self, telegram_id: int):
        res = await self.client.get(f"/users/{telegram_id}")
        if res.status_code == 200:
            return res.json()
        return None

    async def register_user(self, telegram_id: int, full_name: str, group_id: int):
        payload = {
            "telegram_id": telegram_id,
            "full_name": full_name,
            "group_id": group_id
        }
        res = await self.client.post("/users", json=payload)
        return res.status_code in (200, 201)

    async def get_groups(self):
        try:
            res = await self.client.get("/groups")
            if res.status_code == 200:
                return res.json()
            return []
        except Exception:
            return []

    async def create_group(self, title: str):
        try:
            # Передаем 'title', так как бэкенд ожидает поле title
            res = await self.client.post("/groups", json={"title": title})
            if res.status_code in (200, 201):
                return True, res.json()
            return False, res.text
        except Exception as e:
            return False, str(e)

    async def delete_group(self, group_id: int):
        try:
            res = await self.client.delete(f"/groups/{group_id}")
            return res.status_code in (200, 204)
        except Exception:
            return False

    async def update_schedule(self, group_id: int, day_of_week: int, telegram_id: int, lessons: list):
        payload = {
            "telegram_id": telegram_id,
            "lessons": lessons
        }
        res = await self.client.put(f"/schedules/{group_id}/day/{day_of_week}", json=payload)
        return res.status_code == 200

    async def approve_user(self, telegram_id: int, group_id: int, is_approved: bool):
        payload = {
            "is_approved": is_approved,
            "group_id": group_id
        }
        res = await self.client.patch(f"/users/{telegram_id}/approve", json=payload)
        return res.status_code == 200

    async def delete_user(self, telegram_id: int):
        res = await self.client.delete(f"/users/{telegram_id}")
        return res.status_code in (200, 204)

    async def close(self):
        """Закрытие сессии при остановке бота"""
        await self.client.aclose()


api_client = APIClient()