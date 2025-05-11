import sqlite3
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('db_update')

def update_database():
    """Обновляет структуру базы данных для поддержки политических систем"""
    try:
        conn = sqlite3.connect('vpi.db')
        c = conn.cursor()
        
        # Проверяем, есть ли уже колонка political_system
        try:
            c.execute('SELECT political_system FROM players LIMIT 1')
            logger.info("Колонка political_system уже существует.")
        except sqlite3.OperationalError:
            # Колонка не существует, добавляем ее
            c.execute('ALTER TABLE players ADD COLUMN political_system TEXT')
            logger.info("Колонка political_system успешно добавлена в таблицу players.")
        
        # Устанавливаем "democracy" как политическую систему по умолчанию для всех стран
        c.execute('UPDATE players SET political_system = "democracy" WHERE country IS NOT NULL AND (political_system IS NULL OR political_system = "")')
        updated_rows = c.rowcount
        logger.info(f"Установлена 'Демократия' как политическая система по умолчанию для {updated_rows} стран.")
        
        # Показываем текущие страны и их политические системы
        c.execute('SELECT username, country, political_system FROM players WHERE country IS NOT NULL')
        countries = c.fetchall()
        for player in countries:
            logger.info(f"Игрок: {player[0]}, Страна: {player[1]}, Политическая система: {player[2]}")
        
        conn.commit()
        logger.info("Обновление базы данных завершено успешно.")
    except Exception as e:
        logger.error(f"Ошибка при обновлении базы данных: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_database() 