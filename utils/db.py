import sqlite3
from datetime import datetime
import logging
from config.config import FACTORY_PRODUCTION_RATE

logger = logging.getLogger('vpi')

def init_db():
    """Инициализирует базу данных и создает таблицы"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    
    # Создаем таблицу для хранения данных игроков
    c.execute('''CREATE TABLE IF NOT EXISTS players
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  budget INTEGER DEFAULT 1000000,
                  country TEXT,
                  political_system TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Проверяем, нужно ли добавить колонку political_system
    try:
        c.execute('SELECT political_system FROM players LIMIT 1')
    except sqlite3.OperationalError:
        # Колонка не существует, добавляем ее
        c.execute('ALTER TABLE players ADD COLUMN political_system TEXT')
        logger.info("Добавлена колонка political_system в таблицу players")
    
    # Проверяем, нужно ли добавить колонку regions
    try:
        c.execute('SELECT regions FROM players LIMIT 1')
    except sqlite3.OperationalError:
        # Колонка не существует, добавляем ее
        c.execute('ALTER TABLE players ADD COLUMN regions TEXT')
        logger.info("Добавлена колонка regions в таблицу players")
    
    # Создаем таблицу для хранения инвентаря
    c.execute('''CREATE TABLE IF NOT EXISTS inventory
                 (user_id INTEGER,
                  item_type TEXT,
                  quantity INTEGER,
                  FOREIGN KEY (user_id) REFERENCES players(user_id),
                  PRIMARY KEY (user_id, item_type))''')
    
    # Создаем таблицу для хранения истории боев
    c.execute('''CREATE TABLE IF NOT EXISTS battle_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  attacker_id INTEGER,
                  defender_id INTEGER,
                  attacker_troops INTEGER,
                  defender_troops INTEGER,
                  attacker_losses INTEGER,
                  defender_losses INTEGER,
                  winner_id INTEGER,
                  battle_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (attacker_id) REFERENCES players(user_id),
                  FOREIGN KEY (defender_id) REFERENCES players(user_id))''')
    
    # Создаем таблицу для хранения военных заводов пехотного вооружения
    c.execute('''CREATE TABLE IF NOT EXISTS factories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  production_rate INTEGER NOT NULL DEFAULT 1000,
                  last_production TEXT,
                  FOREIGN KEY (user_id) REFERENCES players(user_id))''')
    
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
    
    # Проверяем, есть ли в таблице factories записи с NULL значениями
    c.execute('''SELECT id FROM factories 
                 WHERE production_rate IS NULL OR last_production IS NULL''')
    null_factories = c.fetchall()
    
    # Если есть записи с NULL значениями, обновляем их
    if null_factories:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('''UPDATE factories 
                     SET production_rate = ?, last_production = ? 
                     WHERE production_rate IS NULL OR last_production IS NULL''', 
                  (FACTORY_PRODUCTION_RATE, current_time))
    
    conn.commit()
    conn.close()

# Функции для работы с игроками
def get_player_data(user_id):
    """Получает данные игрока из базы данных"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
    player = c.fetchone()
    conn.close()
    return player

def create_player(user_id, username):
    """Создает нового игрока в базе данных"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO players (user_id, username) VALUES (?, ?)',
              (user_id, username))
    c.execute('INSERT OR IGNORE INTO inventory (user_id, item_type, quantity) VALUES (?, ?, ?)',
              (user_id, 'infantry', 0))
    conn.commit()
    conn.close()

def get_player_country(user_id):
    """Получает страну игрока"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('SELECT country FROM players WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result and result[0] else None

def set_player_country(user_id, country):
    """Устанавливает страну игрока"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('UPDATE players SET country = ? WHERE user_id = ?', (country, user_id))
    conn.commit()
    conn.close()
    
    # Если выбрана страна, инициализируем регионы
    if country:
        initialize_player_regions(user_id, country)

def initialize_player_regions(user_id, country):
    """Инициализирует регионы игрока при выборе страны"""
    from config.regions import COUNTRY_REGIONS
    
    # Получаем список регионов для выбранной страны
    if country not in COUNTRY_REGIONS:
        return
    
    regions = list(COUNTRY_REGIONS[country].keys())
    if not regions:
        return
        
    # Устанавливаем регионы в таблице players
    regions_str = ','.join(regions)
    
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    
    # Обновляем список регионов игрока
    c.execute('UPDATE players SET regions = ? WHERE user_id = ?', 
              (regions_str, user_id))
    
    # Добавляем записи в таблицу country_regions
    for region_id in regions:
        c.execute('''INSERT OR IGNORE INTO country_regions 
                     (user_id, country, region_id, is_controlled, is_damaged, damage_level)
                     VALUES (?, ?, ?, 1, 0, 0)''', 
                  (user_id, country, region_id))
    
    conn.commit()
    conn.close()

def check_has_country(user_id):
    """Проверяет, выбрал ли игрок страну"""
    country = get_player_country(user_id)
    return country is not None

# Функции для работы с политическими системами
def get_player_political_system(user_id):
    """Получает политическую систему игрока"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('SELECT political_system FROM players WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result and result[0] else None

def set_player_political_system(user_id, political_system):
    """Устанавливает политическую систему игрока"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('UPDATE players SET political_system = ? WHERE user_id = ?', (political_system, user_id))
    conn.commit()
    conn.close()

# Получить скорректированное значение производства с учетом политической системы
def get_adjusted_production_rate(user_id, base_rate):
    """Возвращает скорректированное значение производства с учетом политической системы"""
    from config.political_systems import get_political_system_effects
    
    political_system = get_player_political_system(user_id)
    if not political_system:
        return base_rate
    
    effects = get_political_system_effects(political_system)
    
    # Применяем бонусы/штрафы к производству
    modifier = 1.0
    for key, value in effects.items():
        if 'production' in key:
            modifier += value
    
    return int(base_rate * modifier)

# Получить скорректированное значение боевой мощи с учетом политической системы
def get_adjusted_military_power(user_id, base_power):
    """Возвращает скорректированное значение боевой мощи с учетом политической системы"""
    from config.political_systems import get_political_system_effects
    
    political_system = get_player_political_system(user_id)
    if not political_system:
        return base_power
    
    effects = get_political_system_effects(political_system)
    
    # Применяем бонусы/штрафы к боевой мощи
    modifier = 1.0
    for key, value in effects.items():
        if 'military' in key:
            modifier += value
    
    return int(base_power * modifier)

# Функции для работы с экономикой
def update_budget(user_id, new_budget):
    """Обновляет бюджет игрока"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('UPDATE players SET budget = ? WHERE user_id = ?', (new_budget, user_id))
    conn.commit()
    conn.close()

def get_budget(user_id):
    """Получает текущий бюджет игрока"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('SELECT budget FROM players WHERE user_id = ?', (user_id,))
    budget = c.fetchone()
    conn.close()
    return budget[0] if budget else 1000000

# Функции для работы с инвентарем
def update_inventory(user_id, item_type, quantity):
    """Обновляет количество предметов в инвентаре игрока"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('''INSERT INTO inventory (user_id, item_type, quantity)
                 VALUES (?, ?, ?)
                 ON CONFLICT(user_id, item_type) DO UPDATE SET quantity = ?''',
              (user_id, item_type, quantity, quantity))
    conn.commit()
    conn.close()

def get_inventory(user_id):
    """Получает весь инвентарь игрока"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('SELECT item_type, quantity FROM inventory WHERE user_id = ?', (user_id,))
    inventory = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return inventory

# Функции для работы с военными заводами
def get_factories_count(user_id):
    """Получает количество заводов игрока"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM factories WHERE user_id = ?', (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def build_factory(user_id):
    """Строит новый завод для игрока"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT INTO factories (user_id, last_production, production_rate) VALUES (?, ?, ?)', 
             (user_id, current_time, FACTORY_PRODUCTION_RATE))
    conn.commit()
    conn.close()

def calculate_production(user_id):
    """Рассчитывает производство пехотного вооружения за прошедшее время"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    
    # Получаем все заводы игрока
    c.execute('''SELECT last_production, production_rate 
                 FROM factories 
                 WHERE user_id = ?''', (user_id,))
    factories = c.fetchall()
    
    total_production = 0
    current_time = datetime.now()
    current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Получаем модификатор производства от политической системы
    from config.political_systems import get_political_system_effects
    
    political_system = get_player_political_system(user_id)
    production_modifier = 1.0
    
    if political_system:
        effects = get_political_system_effects(political_system)
        for key, value in effects.items():
            if 'production' in key:
                production_modifier += value
    
    for factory in factories:
        # Если last_production NULL, используем текущее время
        if factory[0] is None:
            hours_passed = 0
        else:
            try:
                # Пытаемся преобразовать строку в datetime
                last_production = datetime.strptime(factory[0], '%Y-%m-%d %H:%M:%S')
                hours_passed = (current_time - last_production).total_seconds() / 3600
            except (ValueError, TypeError):
                # Если не удалось преобразовать, считаем что завод только что создан
                hours_passed = 0
        
        # Если production_rate NULL, используем значение по умолчанию
        production_rate = factory[1] if factory[1] is not None else FACTORY_PRODUCTION_RATE
        
        # Применяем модификатор от политической системы
        production_rate = int(production_rate * production_modifier)
        
        production = int(hours_passed * production_rate)
        total_production += production
    
    # Обновляем время последнего производства для всех заводов игрока
    c.execute('''UPDATE factories 
                 SET last_production = ? 
                 WHERE user_id = ?''', (current_time_str, user_id))
    
    conn.commit()
    conn.close()
    return total_production

# Функции для работы с боевой системой
def log_battle(attacker_id, defender_id, attacker_troops, defender_troops,
               attacker_losses, defender_losses, winner_id):
    """Записывает информацию о бое в базу данных"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('''INSERT INTO battle_history
                 (attacker_id, defender_id, attacker_troops, defender_troops,
                  attacker_losses, defender_losses, winner_id)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (attacker_id, defender_id, attacker_troops, defender_troops,
               attacker_losses, defender_losses, winner_id))
    conn.commit()
    conn.close()

def get_battle_history(user_id, limit=5):
    """Получает историю боев игрока"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            bh.battle_date,
            p1.username as attacker,
            p2.username as defender,
            bh.attacker_troops,
            bh.defender_troops,
            bh.attacker_losses,
            bh.defender_losses,
            CASE 
                WHEN bh.winner_id = bh.attacker_id THEN p1.username
                ELSE p2.username
            END as winner
        FROM battle_history bh
        JOIN players p1 ON bh.attacker_id = p1.user_id
        JOIN players p2 ON bh.defender_id = p2.user_id
        WHERE bh.attacker_id = ? OR bh.defender_id = ?
        ORDER BY bh.battle_date DESC
        LIMIT ?
    ''', (user_id, user_id, limit))
    
    battles = c.fetchall()
    conn.close()
    return battles

# Функции для работы с регионами стран
def get_player_regions(user_id):
    """Получает список регионов игрока"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('SELECT regions FROM players WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0]:
        return result[0].split(',')
    else:
        return []

def set_player_regions(user_id, regions_list):
    """Устанавливает список регионов игрока"""
    regions_str = ','.join(regions_list) if regions_list else ''
    
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('UPDATE players SET regions = ? WHERE user_id = ?', (regions_str, user_id))
    conn.commit()
    conn.close()

def get_player_controlled_regions(user_id):
    """Получает детальную информацию о контролируемых регионах игрока"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('''SELECT cr.region_id, cr.is_damaged, cr.damage_level 
                 FROM country_regions cr
                 WHERE cr.user_id = ? AND cr.is_controlled = 1''', (user_id,))
    regions = c.fetchall()
    conn.close()
    
    return regions

def get_region_control_status(user_id, region_id):
    """Проверяет, контролирует ли игрок указанный регион"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('''SELECT is_controlled, is_damaged, damage_level 
                 FROM country_regions 
                 WHERE user_id = ? AND region_id = ?''', (user_id, region_id))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'is_controlled': bool(result[0]),
            'is_damaged': bool(result[1]),
            'damage_level': result[2]
        }
    else:
        return None

def change_region_control(user_id, region_id, is_controlled=True):
    """Изменяет статус контроля региона"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    
    # Обновляем статус контроля региона
    c.execute('''UPDATE country_regions 
                 SET is_controlled = ? 
                 WHERE user_id = ? AND region_id = ?''', 
              (1 if is_controlled else 0, user_id, region_id))
    
    # Обновляем список регионов в players, если статус изменился
    if c.rowcount > 0:
        # Получаем обновленный список контролируемых регионов
        c.execute('''SELECT region_id 
                     FROM country_regions 
                     WHERE user_id = ? AND is_controlled = 1''', (user_id,))
        controlled_regions = [row[0] for row in c.fetchall()]
        
        # Обновляем поле regions
        regions_str = ','.join(controlled_regions)
        c.execute('UPDATE players SET regions = ? WHERE user_id = ?', (regions_str, user_id))
    
    conn.commit()
    conn.close()
    
    return c.rowcount > 0

def set_region_damage(user_id, region_id, is_damaged=True, damage_level=1):
    """Устанавливает статус повреждения региона"""
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('''UPDATE country_regions 
                 SET is_damaged = ?, damage_level = ? 
                 WHERE user_id = ? AND region_id = ?''', 
              (1 if is_damaged else 0, damage_level, user_id, region_id))
    conn.commit()
    conn.close()
    
    return c.rowcount > 0

def repair_region(user_id, region_id):
    """Восстанавливает регион после повреждения"""
    return set_region_damage(user_id, region_id, False, 0)

def get_adjusted_economic_bonus(user_id):
    """Возвращает скорректированный экономический бонус с учетом регионов и политической системы"""
    from config.political_systems import get_political_system_effects
    
    # Получаем бонус от политической системы
    political_system = get_player_political_system(user_id)
    political_modifier = 0.0
    
    if political_system:
        effects = get_political_system_effects(political_system)
        for key, value in effects.items():
            if 'economy' in key:
                political_modifier += value
    
    # Бонусы от регионов нулевые, так как система зданий еще не реализована
    # Когда система зданий будет реализована, регионы будут давать бонусы
    # в зависимости от построенных экономических и военных зданий
    
    return political_modifier

def get_adjusted_production_with_regions(user_id, base_rate):
    """Возвращает скорректированное значение производства с учетом регионов и политической системы"""
    from config.political_systems import get_political_system_effects
    
    # Базовый модификатор от политической системы
    political_system = get_player_political_system(user_id)
    political_modifier = 0.0
    
    if political_system:
        effects = get_political_system_effects(political_system)
        for key, value in effects.items():
            if 'production' in key:
                political_modifier += value
    
    # Бонусы от регионов нулевые, так как система зданий еще не реализована
    # Когда система зданий будет реализована, регионы будут давать бонусы
    # в зависимости от построенных экономических и военных зданий
    
    # Общий модификатор производства - только от политической системы
    total_modifier = 1.0 + political_modifier
    return int(base_rate * total_modifier)

def get_adjusted_military_power_with_regions(user_id, base_power):
    """Возвращает скорректированное значение боевой мощи с учетом регионов и политической системы"""
    from config.political_systems import get_political_system_effects
    
    # Бонус от политической системы
    political_system = get_player_political_system(user_id)
    political_modifier = 0.0
    
    if political_system:
        effects = get_political_system_effects(political_system)
        for key, value in effects.items():
            if 'military' in key:
                political_modifier += value
    
    # Бонусы от регионов нулевые, так как система зданий еще не реализована
    # Когда система зданий будет реализована, регионы будут давать бонусы
    # в зависимости от построенных экономических и военных зданий
    
    # Общий модификатор военной мощи - только от политической системы
    total_modifier = 1.0 + political_modifier
    return int(base_power * total_modifier) 