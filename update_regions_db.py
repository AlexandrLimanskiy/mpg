import sqlite3
import logging
from config.regions import COUNTRY_REGIONS

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('db_update_regions')

def update_database_regions():
    """Обновляет структуру базы данных для поддержки регионов стран"""
    try:
        conn = sqlite3.connect('vpi.db')
        c = conn.cursor()
        
        # Проверяем, есть ли уже колонка regions
        try:
            c.execute('SELECT regions FROM players LIMIT 1')
            logger.info("Колонка regions уже существует.")
        except sqlite3.OperationalError:
            # Колонка не существует, добавляем ее
            c.execute('ALTER TABLE players ADD COLUMN regions TEXT')
            logger.info("Колонка regions успешно добавлена в таблицу players.")
        
        # Создаем таблицу для хранения информации о регионах стран
        c.execute('''CREATE TABLE IF NOT EXISTS country_regions
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER,
                     country TEXT,
                     region_id TEXT,
                     is_controlled BOOLEAN DEFAULT 1,
                     is_damaged BOOLEAN DEFAULT 0,
                     damage_level INTEGER DEFAULT 0,
                     FOREIGN KEY (user_id) REFERENCES players(user_id))''')
        logger.info("Таблица country_regions создана или уже существует.")
        
        # Получаем список всех игроков с выбранными странами
        c.execute('SELECT user_id, username, country FROM players WHERE country IS NOT NULL')
        players = c.fetchall()
        
        # Для каждого игрока с выбранной страной добавляем регионы этой страны
        for player in players:
            user_id, username, country = player
            
            # Проверяем, есть ли уже регионы для этого игрока
            c.execute('SELECT COUNT(*) FROM country_regions WHERE user_id = ?', (user_id,))
            exists = c.fetchone()[0] > 0
            
            if not exists and country in COUNTRY_REGIONS:
                # Добавляем все регионы страны для игрока
                regions = COUNTRY_REGIONS.get(country, {})
                for region_id in regions.keys():
                    c.execute('''INSERT INTO country_regions 
                                (user_id, country, region_id, is_controlled) 
                                VALUES (?, ?, ?, 1)''', 
                              (user_id, country, region_id))
                
                logger.info(f"Добавлены регионы для игрока {username} ({country})")
        
        # Устанавливаем список контролируемых регионов в JSON формате
        for player in players:
            user_id, username, country = player
            if country in COUNTRY_REGIONS:
                c.execute('SELECT region_id FROM country_regions WHERE user_id = ? AND is_controlled = 1', 
                         (user_id,))
                controlled_regions = [row[0] for row in c.fetchall()]
                
                # Преобразуем список в строку с разделителями для хранения
                regions_str = ",".join(controlled_regions)
                
                # Обновляем поле regions в таблице players
                c.execute('UPDATE players SET regions = ? WHERE user_id = ?', 
                         (regions_str, user_id))
                
                logger.info(f"Игрок: {username}, Страна: {country}, Контролируемые регионы: {len(controlled_regions)}")
        
        conn.commit()
        logger.info("Обновление базы данных завершено успешно.")
    except Exception as e:
        logger.error(f"Ошибка при обновлении базы данных: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_regions() 