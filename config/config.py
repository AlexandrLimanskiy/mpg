# Список доступных стран
AVAILABLE_COUNTRIES = ['Украина', 'Россия', 'Беларусь']

# Константы для военных заводов
FACTORY_COST = 100000  # Стоимость постройки завода
FACTORY_PRODUCTION_RATE = 1000  # Производство пехотного вооружения в час
AMMO_PER_INFANTRY = 100  # Количество пехотного вооружения на одного пехотинца

# Стоимость юнитов
INFANTRY_COST = 1000  # Стоимость одного пехотинца 

# Стоимость и требования для новых юнитов
ARTILLERY_COST = 10000  # Стоимость артиллерии
AMMO_PER_ARTILLERY = 500  # Количество пехотного вооружения на артиллерию
ARTILLERY_POWER = 10  # Боевая сила артиллерии (в сравнении с пехотой)

TANK_COST = 50000  # Стоимость танка
AMMO_PER_TANK = 1000  # Количество пехотного вооружения на танк
TANK_POWER = 50  # Боевая сила танка (в сравнении с пехотой)

FIGHTER_COST = 100000  # Стоимость истребителя
AMMO_PER_FIGHTER = 800  # Количество пехотного вооружения на истребитель
FIGHTER_POWER = 80  # Боевая сила истребителя (в сравнении с пехотой)

ASSAULT_COST = 120000  # Стоимость штурмовика
AMMO_PER_ASSAULT = 1500  # Количество пехотного вооружения на штурмовик
ASSAULT_POWER = 100  # Боевая сила штурмовика (в сравнении с пехотой)

BOMBER_COST = 150000  # Стоимость бомбардировщика
AMMO_PER_BOMBER = 2000  # Количество пехотного вооружения на бомбардировщик
BOMBER_POWER = 150  # Боевая сила бомбардировщика (в сравнении с пехотой)

SHIP_COST = 200000  # Стоимость корабля
AMMO_PER_SHIP = 3000  # Количество пехотного вооружения на корабль
SHIP_POWER = 200  # Боевая сила корабля (в сравнении с пехотой)

# Словарь с информацией о всех юнитах для удобства
UNITS_INFO = {
    'infantry': {
        'name': 'Пехота',
        'cost': INFANTRY_COST,
        'ammo': AMMO_PER_INFANTRY,
        'power': 1
    },
    'artillery': {
        'name': 'Артиллерия',
        'cost': ARTILLERY_COST,
        'ammo': AMMO_PER_ARTILLERY,
        'power': ARTILLERY_POWER
    },
    'tank': {
        'name': 'Танк',
        'cost': TANK_COST,
        'ammo': AMMO_PER_TANK,
        'power': TANK_POWER
    },
    'fighter': {
        'name': 'Истребитель',
        'cost': FIGHTER_COST,
        'ammo': AMMO_PER_FIGHTER,
        'power': FIGHTER_POWER
    },
    'assault': {
        'name': 'Штурмовик',
        'cost': ASSAULT_COST,
        'ammo': AMMO_PER_ASSAULT,
        'power': ASSAULT_POWER
    },
    'bomber': {
        'name': 'Бомбардировщик',
        'cost': BOMBER_COST,
        'ammo': AMMO_PER_BOMBER,
        'power': BOMBER_POWER
    },
    'ship': {
        'name': 'Корабль',
        'cost': SHIP_COST,
        'ammo': AMMO_PER_SHIP,
        'power': SHIP_POWER
    }
} 