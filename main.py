import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import random
import sqlite3
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

# Загрузка переменных окружения
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
if not token:
    raise ValueError("Токен бота не найден! Проверьте файл .env")

logger.info(f"Токен загружен: {'*' * len(token)}")

# Настройка интентов бота
intents = discord.Intents.all()  # Включить все интенты

# Создание бота
bot = commands.Bot(command_prefix='/', intents=intents)

# Отключаем стандартную команду help
bot.help_command = None

# Список доступных стран
AVAILABLE_COUNTRIES = ['Украина', 'Россия', 'Беларусь']

# Константы для военных заводов пехотного вооружения
FACTORY_COST = 100000  # Стоимость постройки завода
FACTORY_PRODUCTION_RATE = 1000  # Производство пехотного вооружения в час
AMMO_PER_INFANTRY = 100  # Количество пехотного вооружения на одного пехотинца

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    
    # Создаем таблицу для хранения данных игроков
    c.execute('''CREATE TABLE IF NOT EXISTS players
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  budget INTEGER DEFAULT 1000000,
                  country TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
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
    
    # Создаем таблицу для хранения военных заводов
    c.execute('''CREATE TABLE IF NOT EXISTS factories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  production_rate INTEGER NOT NULL DEFAULT 1000,
                  last_production TEXT,
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

# Функции для работы с базой данных
def get_player_data(user_id):
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
    player = c.fetchone()
    conn.close()
    return player

def create_player(user_id, username):
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO players (user_id, username) VALUES (?, ?)',
              (user_id, username))
    c.execute('INSERT OR IGNORE INTO inventory (user_id, item_type, quantity) VALUES (?, ?, ?)',
              (user_id, 'infantry', 0))
    conn.commit()
    conn.close()

def update_budget(user_id, new_budget):
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('UPDATE players SET budget = ? WHERE user_id = ?', (new_budget, user_id))
    conn.commit()
    conn.close()

def get_budget(user_id):
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('SELECT budget FROM players WHERE user_id = ?', (user_id,))
    budget = c.fetchone()
    conn.close()
    return budget[0] if budget else 1000000

def update_inventory(user_id, item_type, quantity):
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('''INSERT INTO inventory (user_id, item_type, quantity)
                 VALUES (?, ?, ?)
                 ON CONFLICT(user_id, item_type) DO UPDATE SET quantity = ?''',
              (user_id, item_type, quantity, quantity))
    conn.commit()
    conn.close()

def get_inventory(user_id):
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('SELECT item_type, quantity FROM inventory WHERE user_id = ?', (user_id,))
    inventory = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return inventory

def log_battle(attacker_id, defender_id, attacker_troops, defender_troops,
               attacker_losses, defender_losses, winner_id):
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

def get_player_country(user_id):
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('SELECT country FROM players WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result and result[0] else None

def set_player_country(user_id, country):
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('UPDATE players SET country = ? WHERE user_id = ?', (country, user_id))
    conn.commit()
    conn.close()

async def send_private_embed(ctx, embed):
    """Отправляет эмбед только автору команды"""
    try:
        await ctx.author.send(embed=embed)
        if ctx.guild:  # Если команда использована на сервере, а не в личке
            await ctx.message.add_reaction('✅')  # Добавляем реакцию, чтобы показать, что ответ отправлен
    except discord.Forbidden:
        if ctx.guild:
            await ctx.send("Не могу отправить вам личное сообщение. Проверьте настройки приватности.", ephemeral=True)

@bot.event
async def on_ready():
    logger.info(f'Бот {bot.user} успешно запущен!')
    logger.info(f'ID бота: {bot.user.id}')
    
    # Расширенное логирование серверов
    guild_list = []
    for guild in bot.guilds:
        guild_list.append({
            'name': guild.name,
            'id': guild.id,
            'member_count': guild.member_count,
            'is_bot_member': bot.user in guild.members,
            'bot_permissions': guild.get_member(bot.user.id).guild_permissions if guild.get_member(bot.user.id) else None
        })
        logger.info(f'- Сервер: {guild.name} (ID: {guild.id})')
        logger.info(f'  Участников: {guild.member_count}')
        logger.info(f'  Бот в списке участников: {bot.user in guild.members}')
        
        # Проверим разрешения бота на сервере
        bot_member = guild.get_member(bot.user.id)
        if bot_member:
            logger.info(f'  Разрешения бота: {bot_member.guild_permissions}')
    
    logger.info(f'Подключен к серверам: {[g["name"] for g in guild_list]}')
    logger.info(f'Полная информация о серверах: {guild_list}')
    
    # Пробуем получить список всех доступных серверов через HTTP API
    try:
        user_guilds = await bot.http.request(discord.http.Route('GET', '/users/@me/guilds'))
        logger.info(f'Серверы через API: {[g["name"] for g in user_guilds]}')
    except Exception as e:
        logger.error(f'Не удалось получить список серверов через API: {e}')
    
    init_db()
    
    # Загружаем коги
    await load_extensions()

@bot.event
async def on_guild_join(guild):
    logger.info(f'Бот добавлен на сервер: {guild.name} (ID: {guild.id})')
    logger.info(f'Количество участников: {guild.member_count}')
    logger.info(f'Роли бота: {guild.get_member(bot.user.id).roles if guild.get_member(bot.user.id) else "Неизвестно"}')
    logger.info(f'Является ли бот видимым участником: {bot.user in guild.members}')
    
    for member in guild.members:
        if not member.bot:
            create_player(member.id, member.name)
    logger.info(f'Инициализировано игроков: {sum(1 for m in guild.members if not m.bot)}')

# Модифицируем существующие команды для проверки наличия страны
def check_has_country(user_id):
    country = get_player_country(user_id)
    return country is not None

def get_factories_count(user_id):
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM factories WHERE user_id = ?', (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def build_factory(user_id):
    conn = sqlite3.connect('vpi.db')
    c = conn.cursor()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT INTO factories (user_id, last_production, production_rate) VALUES (?, ?, ?)', 
             (user_id, current_time, FACTORY_PRODUCTION_RATE))
    conn.commit()
    conn.close()

def calculate_production(user_id):
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
        
        production = int(hours_passed * production_rate)
        total_production += production
    
    # Обновляем время последнего производства для всех заводов игрока
    c.execute('''UPDATE factories 
                 SET last_production = ? 
                 WHERE user_id = ?''', (current_time_str, user_id))
    
    conn.commit()
    conn.close()
    return total_production

async def load_extensions():
    """Загружает расширения (коги)"""
    extensions = [
        'cogs.country',
        'cogs.economy',
        'cogs.battle',
        'cogs.politics',
        'cogs.regions'
    ]
    
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            logger.info(f"Расширение {ext} успешно загружено")
        except Exception as e:
            logger.error(f"Ошибка при загрузке расширения {ext}: {e}")

# Создаем команду для обработки ошибок команд
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # Проверяем, есть ли команда "shop" в запросе и предлагаем альтернативу
        if "shop" in ctx.message.content:
            await ctx.send("Команда не найдена. Возможно, вы имели в виду `/buy`?", ephemeral=True)
        else:
            await ctx.send(f"Команда не найдена. Используйте `/help_vpi` для просмотра доступных команд.", ephemeral=True)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Ошибка: не указан обязательный аргумент `{error.param.name}`.", ephemeral=True)
    else:
        logger.error(f"Ошибка при выполнении команды {ctx.command}: {error}")
        await ctx.send(f"Произошла ошибка при выполнении команды.", ephemeral=True)

# Запуск бота
try:
    logger.info("Запуск бота...")
    bot.run(token)
except Exception as e:
    logger.error(f"Ошибка при запуске бота: {e}") 