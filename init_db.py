"""
Создаёт таблицы в базе данных.
Запускается ОДИН РАЗ при первом старте.
"""
from database import engine, Base
from models import Game  # не удалять! нужно чтобы модель зарегистрировалась

# Создаём все таблицы
Base.metadata.create_all(bind=engine)

print("=" * 50)
print("Таблицы созданы!")
print("Файл chess.db должен появиться в папке проекта")
print("=" * 50)