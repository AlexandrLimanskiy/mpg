# Политические системы
POLITICAL_SYSTEMS = {
    'democracy': {
        'name': 'Демократия',
        'description': 'Демократическая система управления, власть принадлежит народу.',
        'effects': {
            'production_bonus': 0.1,  # +10% к производству пехотного вооружения
            'economy_bonus': 0.15,    # +15% к доходам экономики
            'military_penalty': -0.05 # -5% к боевой мощи
        },
        'emoji': '🗳️'
    },
    'authoritarianism': {
        'name': 'Авторитаризм',
        'description': 'Авторитарная система управления, власть сосредоточена в руках одного человека.',
        'effects': {
            'production_bonus': 0.05,  # +5% к производству пехотного вооружения
            'economy_bonus': 0.05,     # +5% к доходам экономики
            'military_bonus': 0.1      # +10% к боевой мощи
        },
        'emoji': '👊'
    },
    'military_dictatorship': {
        'name': 'Военная диктатура',
        'description': 'Власть принадлежит военным, приоритет - укрепление армии.',
        'effects': {
            'production_bonus': 0.2,    # +20% к производству пехотного вооружения
            'economy_penalty': -0.1,    # -10% к доходам экономики
            'military_bonus': 0.15      # +15% к боевой мощи
        },
        'emoji': '🪖'
    },
    'communism': {
        'name': 'Коммунизм',
        'description': 'Коммунистическая система управления, нацеленная на равенство.',
        'effects': {
            'production_bonus': 0.15,   # +15% к производству пехотного вооружения
            'economy_penalty': -0.05,   # -5% к доходам экономики
            'military_bonus': 0.05      # +5% к боевой мощи
        },
        'emoji': '☭'
    },
    'monarchy': {
        'name': 'Монархия',
        'description': 'Власть принадлежит монарху, передается по наследству.',
        'effects': {
            'production_penalty': -0.05, # -5% к производству пехотного вооружения
            'economy_bonus': 0.1,        # +10% к доходам экономики
            'military_bonus': 0.05       # +5% к боевой мощи
        },
        'emoji': '👑'
    },
    'anarchy': {
        'name': 'Анархия',
        'description': 'Отсутствие централизованной власти. Каждый сам за себя.',
        'effects': {
            'production_penalty': -0.1,  # -10% к производству пехотного вооружения
            'economy_penalty': -0.15,    # -15% к доходам экономики
            'military_bonus': 0.2        # +20% к боевой мощи
        },
        'emoji': '⚔️'
    }
}

# Получить информацию о политической системе
def get_political_system_info(system_id):
    return POLITICAL_SYSTEMS.get(system_id, None)

# Получить список доступных политических систем
def get_available_political_systems():
    return POLITICAL_SYSTEMS.keys()

# Получить имя политической системы по ID
def get_political_system_name(system_id):
    system = POLITICAL_SYSTEMS.get(system_id)
    return system['name'] if system else "Неизвестно"

# Получить эффекты политической системы
def get_political_system_effects(system_id):
    system = POLITICAL_SYSTEMS.get(system_id)
    return system['effects'] if system else {}

# Форматировать бонус/штраф в процентах для отображения
def format_effect(effect_value):
    if effect_value > 0:
        return f"+{int(effect_value * 100)}%"
    elif effect_value < 0:
        return f"{int(effect_value * 100)}%"
    else:
        return "0%"

# Получить эмодзи и имя политической системы
def get_political_system_emoji_and_name(system_id):
    system = POLITICAL_SYSTEMS.get(system_id)
    if not system:
        return "Не выбрана"
    return f"{system['emoji']} {system['name']}" 