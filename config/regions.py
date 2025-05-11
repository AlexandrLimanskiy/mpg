# Регионы стран
# Эта конфигурация содержит информацию о регионах различных стран.
# Для каждого региона определены его название, описание, особенности и бонусы.

# Украина и её регионы
UKRAINE_REGIONS = {
    'vinnitsa': {
        'name': 'Винницкая область',
        'description': 'Аграрно-промышленный регион в центральной части Украины',
        'effects': {
            'economy_bonus': 0.05,  # +5% к экономике
            'production_bonus': 0.02  # +2% к производству
        },
        'emoji': '🌾',
        'capital': 'Винница'
    },
    'volyn': {
        'name': 'Волынская область',
        'description': 'Западный регион с богатым историческим наследием',
        'effects': {
            'economy_bonus': 0.03,
            'military_bonus': 0.02
        },
        'emoji': '🌲',
        'capital': 'Луцк'
    },
    'dnipro': {
        'name': 'Днепропетровская область',
        'description': 'Важный промышленный и экономический центр',
        'effects': {
            'economy_bonus': 0.1,  # +10% к экономике
            'production_bonus': 0.1  # +10% к производству
        },
        'emoji': '🏭',
        'capital': 'Днепр'
    },
    'donetsk': {
        'name': 'Донецкая область',
        'description': 'Промышленный регион с богатыми угольными месторождениями',
        'effects': {
            'production_bonus': 0.15,  # +15% к производству
            'economy_bonus': 0.07  # +7% к экономике
        },
        'emoji': '⛏️',
        'capital': 'Донецк'
    },
    'zhytomyr': {
        'name': 'Житомирская область',
        'description': 'Северо-западный регион с развитым сельским хозяйством',
        'effects': {
            'economy_bonus': 0.04,
            'production_bonus': 0.02
        },
        'emoji': '🌱',
        'capital': 'Житомир'
    },
    'zakarpattia': {
        'name': 'Закарпатская область',
        'description': 'Западный регион, граничащий с четырьмя странами',
        'effects': {
            'economy_bonus': 0.06,  # Торговые связи
            'military_bonus': 0.03  # Стратегическое положение
        },
        'emoji': '⛰️',
        'capital': 'Ужгород'
    },
    'zaporizhzhia': {
        'name': 'Запорожская область',
        'description': 'Промышленный и энергетический центр',
        'effects': {
            'production_bonus': 0.12,
            'economy_bonus': 0.08
        },
        'emoji': '⚡',
        'capital': 'Запорожье'
    },
    'ivano_frankivsk': {
        'name': 'Ивано-Франковская область',
        'description': 'Западный регион с развитым туризмом',
        'effects': {
            'economy_bonus': 0.07,
            'military_bonus': 0.02
        },
        'emoji': '🏔️',
        'capital': 'Ивано-Франковск'
    },
    'kyiv_region': {
        'name': 'Киевская область',
        'description': 'Центральный регион, окружающий столицу',
        'effects': {
            'economy_bonus': 0.1,
            'production_bonus': 0.05,
            'military_bonus': 0.05
        },
        'emoji': '🏙️',
        'capital': 'Киев'
    },
    'kirovohrad': {
        'name': 'Кировоградская область',
        'description': 'Центральный аграрный регион',
        'effects': {
            'economy_bonus': 0.05,
            'production_bonus': 0.03
        },
        'emoji': '🌿',
        'capital': 'Кропивницкий'
    },
    'luhansk': {
        'name': 'Луганская область',
        'description': 'Восточный промышленный регион',
        'effects': {
            'production_bonus': 0.12,
            'economy_bonus': 0.06
        },
        'emoji': '🏗️',
        'capital': 'Луганск'
    },
    'lviv': {
        'name': 'Львовская область',
        'description': 'Западный культурный и туристический центр',
        'effects': {
            'economy_bonus': 0.09,
            'military_bonus': 0.04
        },
        'emoji': '🏰',
        'capital': 'Львов'
    },
    'mykolaiv': {
        'name': 'Николаевская область',
        'description': 'Южный регион с выходом к Черному морю и развитым судостроением',
        'effects': {
            'production_bonus': 0.08,
            'economy_bonus': 0.07,
            'military_bonus': 0.05  # Военно-морской бонус
        },
        'emoji': '⚓',
        'capital': 'Николаев'
    },
    'odesa': {
        'name': 'Одесская область',
        'description': 'Южный регион с крупнейшим морским портом',
        'effects': {
            'economy_bonus': 0.12,  # +12% к экономике (торговля)
            'military_bonus': 0.06  # Военно-морской бонус
        },
        'emoji': '🚢',
        'capital': 'Одесса'
    },
    'poltava': {
        'name': 'Полтавская область',
        'description': 'Центральный регион с развитой промышленностью и сельским хозяйством',
        'effects': {
            'economy_bonus': 0.07,
            'production_bonus': 0.06
        },
        'emoji': '🏞️',
        'capital': 'Полтава'
    },
    'rivne': {
        'name': 'Ровенская область',
        'description': 'Северо-западный регион с лесными ресурсами',
        'effects': {
            'economy_bonus': 0.04,
            'production_bonus': 0.03
        },
        'emoji': '🌳',
        'capital': 'Ровно'
    },
    'sumy': {
        'name': 'Сумская область',
        'description': 'Северо-восточный пограничный регион',
        'effects': {
            'economy_bonus': 0.05,
            'military_bonus': 0.04  # Приграничное положение
        },
        'emoji': '🌄',
        'capital': 'Сумы'
    },
    'ternopil': {
        'name': 'Тернопольская область',
        'description': 'Западный аграрный регион',
        'effects': {
            'economy_bonus': 0.04,
            'production_bonus': 0.02
        },
        'emoji': '🌽',
        'capital': 'Тернополь'
    },
    'kharkiv': {
        'name': 'Харьковская область',
        'description': 'Научный и промышленный центр на востоке',
        'effects': {
            'economy_bonus': 0.09,
            'production_bonus': 0.09,
            'military_bonus': 0.05  # Военная промышленность
        },
        'emoji': '🔬',
        'capital': 'Харьков'
    },
    'kherson': {
        'name': 'Херсонская область',
        'description': 'Южный регион с сельским хозяйством и выходом к морю',
        'effects': {
            'economy_bonus': 0.06,
            'military_bonus': 0.03
        },
        'emoji': '🌊',
        'capital': 'Херсон'
    },
    'khmelnytskyi': {
        'name': 'Хмельницкая область',
        'description': 'Западно-центральный регион с разнообразной экономикой',
        'effects': {
            'economy_bonus': 0.05,
            'production_bonus': 0.04
        },
        'emoji': '🏘️',
        'capital': 'Хмельницкий'
    },
    'cherkasy': {
        'name': 'Черкасская область',
        'description': 'Центральный регион с историческим значением',
        'effects': {
            'economy_bonus': 0.06,
            'production_bonus': 0.04
        },
        'emoji': '🏞️',
        'capital': 'Черкассы'
    },
    'chernihiv': {
        'name': 'Черниговская область',
        'description': 'Северный регион с древней историей',
        'effects': {
            'economy_bonus': 0.04,
            'military_bonus': 0.03
        },
        'emoji': '🏯',
        'capital': 'Чернигов'
    },
    'chernivtsi': {
        'name': 'Черновицкая область',
        'description': 'Юго-западный многонациональный регион',
        'effects': {
            'economy_bonus': 0.05,
            'military_bonus': 0.02
        },
        'emoji': '🏡',
        'capital': 'Черновцы'
    },
    'crimea': {
        'name': 'Крым',
        'description': 'Полуостров с уникальным климатом и стратегическим положением',
        'effects': {
            'economy_bonus': 0.08,  # Туризм
            'military_bonus': 0.07  # Стратегическое положение
        },
        'emoji': '🌴',
        'capital': 'Симферополь'
    },
    'kyiv_city': {
        'name': 'Киев',
        'description': 'Столица Украины, крупнейший политический и экономический центр',
        'effects': {
            'economy_bonus': 0.15,  # +15% к экономике
            'production_bonus': 0.1,  # +10% к производству
            'military_bonus': 0.1  # +10% к военной мощи
        },
        'emoji': '🏛️',
        'capital': 'Киев',
        'is_capital': True
    },
    'sevastopol': {
        'name': 'Севастополь',
        'description': 'Город особого значения, важный морской порт',
        'effects': {
            'economy_bonus': 0.06,
            'military_bonus': 0.08  # Военно-морская база
        },
        'emoji': '⚓',
        'capital': 'Севастополь'
    }
}

# Словарь для быстрого доступа к регионам по стране
COUNTRY_REGIONS = {
    'Украина': UKRAINE_REGIONS,
    # В будущем здесь будут регионы других стран
}

# Получить информацию о регионе
def get_region_info(country, region_id):
    """Возвращает информацию о регионе по ID"""
    regions = COUNTRY_REGIONS.get(country, {})
    return regions.get(region_id, None)

# Получить список доступных регионов для страны
def get_available_regions(country):
    """Возвращает список доступных регионов для указанной страны"""
    return COUNTRY_REGIONS.get(country, {}).keys()

# Получить название региона по ID
def get_region_name(country, region_id):
    """Возвращает название региона по ID"""
    region = get_region_info(country, region_id)
    return region['name'] if region else "Неизвестно"

# Получить эффекты региона
def get_region_effects(country, region_id):
    """Возвращает эффекты региона"""
    region = get_region_info(country, region_id)
    return region['effects'] if region else {}

# Форматировать бонус/штраф в процентах для отображения
def format_effect(effect_value):
    """Форматирует значение эффекта в процентах"""
    if effect_value > 0:
        return f"+{int(effect_value * 100)}%"
    elif effect_value < 0:
        return f"{int(effect_value * 100)}%"
    else:
        return "0%"

# Получить эмодзи и имя региона
def get_region_emoji_and_name(country, region_id):
    """Возвращает эмодзи и имя региона"""
    region = get_region_info(country, region_id)
    if not region:
        return "Неизвестный регион"
    return f"{region['emoji']} {region['name']}"

# Проверить, является ли регион столицей
def is_capital_region(country, region_id):
    """Проверяет, является ли регион столицей"""
    region = get_region_info(country, region_id)
    return region.get('is_capital', False) if region else False 