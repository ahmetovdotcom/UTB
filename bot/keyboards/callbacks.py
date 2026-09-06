from aiogram.filters.callback_data import CallbackData

class GroupPagination(CallbackData, prefix="groups"):
    page: int
    action: str  # "prev", "next", "select"
    group_id: int = 0