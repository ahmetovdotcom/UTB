import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

# Читаем секретный ключ из переменных окружения бэкенда (.env файла)
API_SECRET_KEY = settings.API_SECRET_KEY

# Используем стандартный схемный интерфейс FastAPI для Bearer токенов
security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Зависимость для защиты защищенных эндпоинтов.
    Проверяет, соответствует ли переданный Bearer токен ключу API_SECRET_KEY.
    """
    if credentials.credentials != API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или отсутствующий API Secret Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials