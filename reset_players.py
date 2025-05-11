import sqlite3
import logging
import sys
from utils.db import initialize_player_regions

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger()

def reset_all_player_data():
    """Сбрасывает все данные игроков в базе данных"""
    try:
        conn = sqlite3.connect('vpi.db')
        c = conn.cursor()
        
        # Запрашиваем подтверждение перед сбросом данных
        if len(sys.argv) <= 1 or sys.argv[1] != "--confirm":
            logger.warning("⚠️ ВНИМАНИЕ! Это действие сбросит ВСЕ данные игроков!")
            logger.warning("Чтобы подтвердить сброс, запустите скрипт с параметром --confirm")
            return
        
        # Сначала получаем количество игроков
        c.execute('SELECT COUNT(*) FROM players')
        player_count = c.fetchone()[0]
        
        # Очищаем таблицу игроков (сохраняем, но сбрасываем данные)
        c.execute('''UPDATE players SET 
                      budget = 1000000,
                      country = NULL,
                      political_system = NULL,
                      regions = NULL''')
        
        # Очищаем инвентарь
        c.execute('DELETE FROM inventory')
        
        # Очищаем заводы
        c.execute('DELETE FROM factories')
        
        # Очищаем историю боев
        c.execute('DELETE FROM battle_history')
        
        # Очищаем информацию о регионах
        c.execute('DELETE FROM country_regions')
        
        # Фиксируем изменения
        conn.commit()
        
        logger.info(f"✅ Данные {player_count} игроков успешно сброшены!")
        
    except sqlite3.Error as e:
        logger.error(f"Ошибка при сбросе данных: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def reinitialize_missing_regions():
    """Переинициализирует регионы для игроков, которые имеют страну, но не имеют регионов"""
    try:
        conn = sqlite3.connect('vpi.db')
        c = conn.cursor()
        
        # Ищем игроков у которых есть страна, но нет регионов
        c.execute('SELECT user_id, country FROM players WHERE country IS NOT NULL AND (regions IS NULL OR regions = "")')
        players = c.fetchall()
        
        if not players:
            logger.info("Нет игроков с отсутствующими регионами.")
            return
        
        # Инициализируем регионы для каждого найденного игрока
        fixed_count = 0
        for user_id, country in players:
            initialize_player_regions(user_id, country)
            fixed_count += 1
        
        logger.info(f"✅ Регионы восстановлены для {fixed_count} игроков.")
        
    except sqlite3.Error as e:
        logger.error(f"Ошибка при восстановлении регионов: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # При запуске с аргументом --check-regions только проверяем и восстанавливаем регионы
    if len(sys.argv) > 1 and sys.argv[1] == "--check-regions":
        reinitialize_missing_regions()
    else:
        reset_all_player_data() 