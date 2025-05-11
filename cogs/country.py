import discord
from discord.ext import commands
import logging
from utils.db import (get_player_country, set_player_country, create_player, check_has_country, 
                     get_player_political_system, get_budget, get_inventory, get_factories_count, 
                     get_player_data, get_adjusted_military_power, calculate_production,
                     get_player_regions, get_region_control_status, get_adjusted_military_power_with_regions,
                     get_adjusted_production_with_regions, get_player_controlled_regions)
from config.config import AVAILABLE_COUNTRIES, UNITS_INFO, FACTORY_PRODUCTION_RATE
from config.political_systems import get_political_system_emoji_and_name, get_political_system_info, format_effect, get_political_system_effects
from config.regions import get_region_info, format_effect as region_format_effect, COUNTRY_REGIONS

logger = logging.getLogger('vpi')

# Список администраторов, имеющих доступ к админ-командам
ADMIN_USERNAMES = ['yankeedesu', 'whymonty']

# Базовый класс с кнопкой закрытия
class CloseView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=120)  # 2 минуты таймаут
        self.ctx = ctx
        self.message = None
    
    @discord.ui.button(label="❌ Закрыть", style=discord.ButtonStyle.red, custom_id="close", row=1)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Эта кнопка не для вас.", ephemeral=True)
            return
        await interaction.message.delete()
    
    async def on_timeout(self):
        # Автоматическое удаление сообщения после истечения таймаута
        if self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                # Сообщение уже удалено
                pass

# Расширенный класс с кнопкой статистики регионов
class CountryView(CloseView):
    def __init__(self, ctx, player_id, country):
        super().__init__(ctx)
        self.player_id = player_id
        self.country = country
    
    @discord.ui.button(label="🌆 Статистика регионов", style=discord.ButtonStyle.primary, custom_id="region_stats", row=0)
    async def region_stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Эта кнопка не для вас.", ephemeral=True)
            return
        
        # Получаем список регионов игрока
        regions = get_player_regions(self.player_id)
        
        if not regions:
            await interaction.response.send_message(
                f"У вас нет контролируемых регионов в стране {self.country}.",
                ephemeral=True
            )
            return
        
        # Получаем детальную информацию о регионах
        regions_details = get_player_controlled_regions(self.player_id)
        
        # Обрабатываем все регионы
        processed_regions = []
        for region_id, is_damaged, damage_level in regions_details:
            region_info = get_region_info(self.country, region_id)
            if not region_info:
                continue
                
            region_status = "🟢 Нормальное состояние"
            if is_damaged:
                damage_percent = int(damage_level * 25)
                region_status = f"🔴 Поврежден (уровень {damage_level}/4, -{damage_percent}% эффективность)"
            
            region_text = f"**Столица**: {region_info['capital']}\n"
            region_text += f"**Статус**: {region_status}\n"
            
            # Добавляем информацию о построенных зданиях
            region_text += "**Постройки**: Пока нет построенных зданий\n"
            
            # Добавляем информацию о производстве (заглушка до реализации системы зданий)
            region_text += "**Производство**: Будет доступно после реализации системы зданий\n"
            
            # Добавляем потенциальные эффекты региона (в настоящее время не активны)
            effects_text = []
            for effect_key, effect_value in region_info['effects'].items():
                if 'production' in effect_key:
                    effects_text.append(f"Производство: {region_format_effect(effect_value)}")
                elif 'economy' in effect_key:
                    effects_text.append(f"Экономика: {region_format_effect(effect_value)}")
                elif 'military' in effect_key:
                    effects_text.append(f"Военная мощь: {region_format_effect(effect_value)}")
            
            if effects_text:
                region_text += "**Потенциальные бонусы** (не активны до строительства зданий): " + ", ".join(effects_text)
            
            processed_regions.append({
                'name': f"{region_info['emoji']} {region_info['name']}",
                'value': region_text,
                'inline': False
            })
        
        # Разбиваем регионы на страницы (максимум 24 поля на страницу, оставляем место для навигации)
        MAX_FIELDS = 24
        pages = []
        for i in range(0, len(processed_regions), MAX_FIELDS):
            pages.append(processed_regions[i:i + MAX_FIELDS])
            
        # Создаем первую страницу
        current_page = 0
        total_pages = len(pages)
            
        # Формируем эмбед с информацией
        embed = discord.Embed(
            title=f"Статистика регионов | {self.country}",
            description=f"Детальная информация о ваших регионах (страница {current_page + 1}/{total_pages})\n\n**💡 Примечание:** Система экономических и военных построек в регионах находится в разработке и скоро будет добавлена!",
            color=discord.Color.blue()
        )
        
        # Добавляем поля для текущей страницы
        for field in pages[current_page]:
            embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])
        
        # Добавляем информацию о будущей системе зданий
        embed.set_footer(text="Скоро будет добавлена система экономических и военных построек в регионах!")
        
        # Отправляем сообщение с новой кнопкой для возврата
        view = RegionStatsWithPaginationView(self.ctx, self.player_id, self.country, pages, current_page)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        view.message = await interaction.original_response()

# Класс для просмотра статистики регионов с кнопками навигации
class RegionStatsWithPaginationView(CloseView):
    def __init__(self, ctx, player_id, country, pages, current_page=0):
        super().__init__(ctx)
        self.player_id = player_id
        self.country = country
        self.pages = pages
        self.current_page = current_page
        self.total_pages = len(pages)
        
        # Добавляем кнопки навигации, если больше одной страницы
        if self.total_pages > 1:
            # Предыдущая страница
            prev_button = discord.ui.Button(label="◀️", style=discord.ButtonStyle.secondary, custom_id="prev_page", row=0, disabled=(current_page == 0))
            prev_button.callback = self.prev_page_callback
            self.add_item(prev_button)
            
            # Следующая страница
            next_button = discord.ui.Button(label="▶️", style=discord.ButtonStyle.secondary, custom_id="next_page", row=0, disabled=(current_page == self.total_pages - 1))
            next_button.callback = self.next_page_callback
            self.add_item(next_button)
    
    @discord.ui.button(label="🔙 Вернуться к информации о стране", style=discord.ButtonStyle.green, custom_id="back", row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Эта кнопка не для вас.", ephemeral=True)
            return
        
        # Удаляем текущее сообщение
        await interaction.message.delete()
        
        # Создаем новую команду my_country
        await self.ctx.bot.get_command('my_country').callback(self.ctx)
    
    async def prev_page_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Эта кнопка не для вас.", ephemeral=True)
            return
        
        self.current_page = max(0, self.current_page - 1)
        await self.update_page(interaction)
    
    async def next_page_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Эта кнопка не для вас.", ephemeral=True)
            return
        
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        await self.update_page(interaction)
    
    async def update_page(self, interaction):
        # Формируем эмбед с информацией
        embed = discord.Embed(
            title=f"Статистика регионов | {self.country}",
            description=f"Детальная информация о ваших регионах (страница {self.current_page + 1}/{self.total_pages})\n\n**💡 Примечание:** Система экономических и военных построек в регионах находится в разработке и скоро будет добавлена!",
            color=discord.Color.blue()
        )
        
        # Добавляем поля для текущей страницы
        for field in self.pages[self.current_page]:
            embed.add_field(name=field['name'], value=field['value'], inline=field['inline'])
        
        # Добавляем информацию о будущей системе зданий
        embed.set_footer(text="Скоро будет добавлена система экономических и военных построек в регионах!")
        
        # Обновляем состояние кнопок
        for child in self.children:
            if child.custom_id == "prev_page":
                child.disabled = (self.current_page == 0)
            elif child.custom_id == "next_page":
                child.disabled = (self.current_page == self.total_pages - 1)
        
        # Обновляем сообщение
        await interaction.response.edit_message(embed=embed, view=self)

# Класс для просмотра статистики регионов с кнопкой возврата
class RegionStatsView(CloseView):
    def __init__(self, ctx, player_id, country):
        super().__init__(ctx)
        self.player_id = player_id
        self.country = country
    
    @discord.ui.button(label="🔙 Вернуться к информации о стране", style=discord.ButtonStyle.green, custom_id="back", row=0)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Эта кнопка не для вас.", ephemeral=True)
            return
        
        # Удаляем текущее сообщение
        await interaction.message.delete()
        
        # Создаем новую команду my_country
        await self.ctx.bot.get_command('my_country').callback(self.ctx)

class CountryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def is_admin(self, ctx):
        """Проверка, является ли пользователь администратором"""
        return ctx.author.name.lower() in [name.lower() for name in ADMIN_USERNAMES]
    
    @commands.command(name='select_country')
    async def select_country(self, ctx, country: str = None):
        """Выбор страны для игры"""
        # Проверяем, есть ли у игрока уже выбранная страна
        current_country = get_player_country(ctx.author.id)
        if current_country:
            embed = discord.Embed(
                title="Ошибка выбора страны",
                description=f"Вы уже выбрали страну: {current_country}. Сменить страну нельзя!",
                color=discord.Color.red()
            )
            view = CloseView(ctx)
            message = await ctx.send(embed=embed, view=view, ephemeral=True)
            view.message = message
            return

        if not country:
            # Показываем список доступных стран
            embed = discord.Embed(
                title="Выбор страны",
                description="Выберите страну командой `/select_country [название]`",
                color=discord.Color.blue()
            )
            
            countries_list = "\n".join(AVAILABLE_COUNTRIES)
            embed.add_field(
                name="Доступные страны:",
                value=countries_list,
                inline=False
            )
            
            view = CloseView(ctx)
            message = await ctx.send(embed=embed, view=view, ephemeral=True)
            view.message = message
            return

        # Проверяем правильность названия страны
        if country not in AVAILABLE_COUNTRIES:
            embed = discord.Embed(
                title="Ошибка выбора страны",
                description=f"Неверное название страны. Доступные страны:\n{', '.join(AVAILABLE_COUNTRIES)}",
                color=discord.Color.red()
            )
            view = CloseView(ctx)
            message = await ctx.send(embed=embed, view=view, ephemeral=True)
            view.message = message
            return

        # Создаем игрока, если его нет в базе
        create_player(ctx.author.id, ctx.author.name)
        
        # Устанавливаем страну
        set_player_country(ctx.author.id, country)
        
        embed = discord.Embed(
            title="Страна выбрана!",
            description=f"Вы теперь играете за {country}",
            color=discord.Color.green()
        )
        
        # Получаем регионы игрока
        regions = get_player_regions(ctx.author.id)
        controlled_regions_count = len(regions) if regions else 0
        
        if controlled_regions_count > 0:
            embed.add_field(
                name="🌆 Регионы инициализированы",
                value=f"Вам автоматически назначены все {controlled_regions_count} регионов страны {country}.",
                inline=False
            )
            
            # Добавляем поле с информацией о будущей системе зданий
            embed.add_field(
                name="💡 Система зданий",
                value="В будущем обновлении вы сможете строить экономические и военные здания в регионах для получения бонусов.",
                inline=False
            )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
    
    @commands.command(name='set_country')
    async def set_country(self, ctx, target: discord.Member, country: str):
        """[ADMIN] Назначить страну игроку"""
        # Проверяем, является ли пользователь администратором
        if not await self.is_admin(ctx):
            await ctx.send("У вас нет прав для использования этой команды.", ephemeral=True)
            return
        
        # Проверяем правильность названия страны
        if country not in AVAILABLE_COUNTRIES:
            await ctx.send(
                f"Неверное название страны. Доступные страны:\n{', '.join(AVAILABLE_COUNTRIES)}", 
                ephemeral=True
            )
            return
        
        # Создаем игрока, если его нет в базе
        create_player(target.id, target.name)
        
        # Устанавливаем страну
        set_player_country(target.id, country)
        
        embed = discord.Embed(
            title="Страна назначена администратором",
            description=f"Администратор {ctx.author.name} назначил игроку {target.name} страну {country}",
            color=discord.Color.gold()
        )
        
        # Получаем регионы игрока
        regions = get_player_regions(target.id)
        controlled_regions_count = len(regions) if regions else 0
        
        if controlled_regions_count > 0:
            embed.add_field(
                name="🌆 Регионы инициализированы",
                value=f"Игроку автоматически назначены все {controlled_regions_count} регионов страны {country}.",
                inline=False
            )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
        
        # Отправляем уведомление игроку
        try:
            player_embed = discord.Embed(
                title="🗺️ Страна назначена!",
                description=f"Администратор {ctx.author.name} назначил вам страну {country}",
                color=discord.Color.green()
            )
            
            player_view = CloseView(ctx)
            player_message = await target.send(embed=player_embed, view=player_view)
            player_view.message = player_message
        except discord.Forbidden:
            await ctx.send(f"Не удалось отправить уведомление игроку {target.name} (личные сообщения закрыты)")
    
    @commands.command(name='reset_country')
    async def reset_country(self, ctx, target: discord.Member):
        """[ADMIN] Сбросить выбор страны игрока"""
        # Проверяем, является ли пользователь администратором
        if not await self.is_admin(ctx):
            await ctx.send("У вас нет прав для использования этой команды.", ephemeral=True)
            return
        
        # Создаем игрока, если его нет в базе
        create_player(target.id, target.name)
        
        # Сбрасываем страну игрока
        set_player_country(target.id, None)
        
        embed = discord.Embed(
            title="Сброс страны",
            description=f"Администратор {ctx.author.name} сбросил выбор страны игрока {target.name}",
            color=discord.Color.gold()
        )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
        
        # Отправляем уведомление игроку
        try:
            player_embed = discord.Embed(
                title="🗺️ Страна сброшена!",
                description=f"Администратор {ctx.author.name} сбросил выбранную вами страну. Вы можете выбрать новую страну командой `/select_country`",
                color=discord.Color.orange()
            )
            
            player_view = CloseView(ctx)
            player_message = await target.send(embed=player_embed, view=player_view)
            player_view.message = player_message
        except discord.Forbidden:
            await ctx.send(f"Не удалось отправить уведомление игроку {target.name} (личные сообщения закрыты)")

    @commands.command(name='my_country')
    async def show_country(self, ctx):
        """Показывает информацию о стране игрока"""
        player_id = ctx.author.id
        country = get_player_country(player_id)
        
        if not country:
            await ctx.send(
                "Вы еще не выбрали страну. Используйте команду `/select_country` для выбора.", 
                ephemeral=True
            )
            return
        
        # Получаем политическую систему
        political_system = get_player_political_system(player_id)
        
        # Получаем статистику игрока
        budget = get_budget(player_id)
        inventory = get_inventory(player_id)
        factories_count = get_factories_count(player_id)
        
        # Получаем информацию о регионах игрока
        regions = get_player_regions(player_id)
        controlled_regions_count = len(regions) if regions else 0
        
        # Рассчитываем боевую мощь
        total_power = 0
        for unit_type, count in inventory.items():
            if unit_type in UNITS_INFO:
                unit_power = count * UNITS_INFO[unit_type]['power']
                total_power += unit_power
        
        # Применяем модификатор боевой мощи от политической системы и регионов
        total_power = get_adjusted_military_power_with_regions(player_id, total_power)
        
        # Создаем красивый эмбед для отображения информации о стране
        embed = discord.Embed(
            title=f"🗺️ Информация о стране | {country}",
            description=f"Подробная информация о вашей стране и статистика",
            color=discord.Color.from_rgb(0, 102, 204)  # Голубой цвет
        )
        
        # Добавляем изображение флага (если есть)
        flag_urls = {
            'Украина': 'https://upload.wikimedia.org/wikipedia/commons/4/49/Flag_of_Ukraine.svg',
            'Россия': 'https://upload.wikimedia.org/wikipedia/commons/f/f3/Flag_of_Russia.svg',
            'Беларусь': 'https://upload.wikimedia.org/wikipedia/commons/8/85/Flag_of_Belarus.svg',
        }
        
        if country in flag_urls:
            embed.set_thumbnail(url=flag_urls[country])
        
        # Основная информация
        embed.add_field(
            name="🏛️ Политическая система",
            value=f"{get_political_system_emoji_and_name(political_system) if political_system else 'Не выбрана - используйте `/set_political_system`'}",
            inline=False
        )
        
        # Если есть политическая система, добавляем описание ее эффектов
        if political_system:
            system_info = get_political_system_info(political_system)
            
            effects_text = ""
            for effect_key, effect_value in system_info['effects'].items():
                if 'production' in effect_key:
                    effects_text += f"• Производство: {format_effect(effect_value)}\n"
                elif 'economy' in effect_key:
                    effects_text += f"• Экономика: {format_effect(effect_value)}\n"
                elif 'military' in effect_key:
                    effects_text += f"• Боевая мощь: {format_effect(effect_value)}\n"
            
            embed.add_field(
                name="📊 Эффекты политической системы",
                value=effects_text or "Нет эффектов",
                inline=False
            )
        
        # Добавляем информацию о регионах
        if controlled_regions_count > 0:
            # Получаем список поврежденных регионов
            damaged_regions_count = 0
            regions_effects = {
                'economy': 0.0,
                'production': 0.0,
                'military': 0.0
            }
            
            # Суммируем эффекты от всех регионов
            for region_id in regions:
                region_info = get_region_info(country, region_id)
                if region_info:
                    # Проверяем, поврежден ли регион
                    region_status = get_region_control_status(player_id, region_id)
                    if region_status and region_status['is_damaged']:
                        damaged_regions_count += 1
                        damage_factor = max(0.0, 1.0 - (region_status['damage_level'] * 0.25))
                    else:
                        damage_factor = 1.0
                    
                    # Добавляем эффекты региона с учетом повреждений
                    for effect_key, effect_value in region_info['effects'].items():
                        if 'production' in effect_key:
                            regions_effects['production'] += effect_value * damage_factor
                        elif 'economy' in effect_key:
                            regions_effects['economy'] += effect_value * damage_factor
                        elif 'military' in effect_key:
                            regions_effects['military'] += effect_value * damage_factor
            
            # Форматируем эффекты регионов для отображения
            regions_text = f"Контролируемые регионы: {controlled_regions_count}/{len(COUNTRY_REGIONS.get(country, {}))}\n"
            if damaged_regions_count > 0:
                regions_text += f"⚠️ Повреждено регионов: {damaged_regions_count}\n"
            
            regions_text += "\n**Суммарные бонусы от регионов:**\n"
            
            # Временно отключены бонусы от регионов до реализации системы зданий
            regions_text += "❗ Бонусы регионов временно неактивны до реализации системы экономических и военных построек\n"
            regions_text += "После внедрения системы зданий, регионы будут давать следующие бонусы:\n"
            
            for effect_key, effect_value in regions_effects.items():
                if effect_value != 0:
                    if effect_key == 'production':
                        regions_text += f"• Производство: {region_format_effect(effect_value)}\n"
                    elif effect_key == 'economy':
                        regions_text += f"• Экономика: {region_format_effect(effect_value)}\n"
                    elif effect_key == 'military':
                        regions_text += f"• Боевая мощь: {region_format_effect(effect_value)}\n"
            
            embed.add_field(
                name="🌆 Регионы",
                value=regions_text + "\nИспользуйте `/regions` для подробной информации.",
                inline=False
            )
        else:
            embed.add_field(
                name="🌆 Регионы",
                value=f"У вас нет контролируемых регионов.\nИспользуйте `/country_regions` для просмотра регионов страны {country}.",
                inline=False
            )
        
        # Экономика
        embed.add_field(
            name="💰 Бюджет",
            value=f"{budget:,}$",
            inline=True
        )
        
        # Производство
        if factories_count > 0:
            base_production = factories_count * FACTORY_PRODUCTION_RATE
            
            production_text = f"{factories_count} завод(ов)\n"
            
            # Базовое производство
            production_text += f"Базовое производство: {base_production} ед./час\n"
            
            # Бонусы от политической системы и регионов
            adjusted_production = get_adjusted_production_with_regions(player_id, base_production)
            
            if adjusted_production != base_production:
                bonus_percent = ((adjusted_production / base_production) - 1.0) * 100
                sign = "+" if bonus_percent > 0 else ""
                production_text += f"Итоговое производство с учетом бонусов: {adjusted_production} ед./час ({sign}{bonus_percent:.1f}%)\n"
            
            embed.add_field(
                name="🏭 Производство пехотного вооружения",
                value=production_text,
                inline=True
            )
        
        # Военная мощь
        military_text = f"Общая боевая мощь: {total_power:,}\n\n"
        
        # Добавляем подробную информацию о военных юнитах
        unit_counts = []
        for unit_type, info in UNITS_INFO.items():
            count = inventory.get(unit_type, 0)
            if count > 0:
                unit_counts.append(f"{info['name']}: {count:,}")
        
        if unit_counts:
            military_text += "**Военные юниты:**\n" + "\n".join(unit_counts)
        else:
            military_text += "*Нет военных юнитов*"
        
        embed.add_field(
            name="⚔️ Военная статистика",
            value=military_text,
            inline=False
        )
        
        # Запасы пехотного вооружения
        embed.add_field(
            name="🧨 Пехотное вооружение",
            value=f"{inventory.get('ammo', 0):,} единиц",
            inline=True
        )
        
        # Добавляем футер с дополнительной информацией
        player_data = get_player_data(player_id)
        if player_data and player_data[4]:  # Индекс 4 - created_at
            created_at = player_data[4]
            embed.set_footer(text=f"Страна основана: {created_at}")
        
        view = CountryView(ctx, player_id, country)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
    
    @commands.command(name='help_vpi')
    async def show_help(self, ctx):
        """Показывает справку по игровым командам"""
        is_admin = await self.is_admin(ctx)
        
        # Основной эмбед с общей информацией
        main_embed = discord.Embed(
            title="🎮 Военно-Политическая Игра | Помощь",
            description="Добро пожаловать в ВПИ - военно-политическую игру для Discord!\n\n"
                        "Выберите страну, развивайте экономику, создавайте армию и ведите войны с другими игроками.",
            color=discord.Color.blue()
        )
        
        # Добавляем картинку в эмбед, если она есть
        main_embed.set_thumbnail(url="https://i.imgur.com/ZpUZ6Nm.png")
        
        # Добавляем поле с категориями команд
        main_embed.add_field(
            name="📋 Категории команд",
            value="🗺️ Управление страной\n"
                  "💰 Экономика\n"
                  "🛒 Военная техника\n"
                  "⚔️ Военные действия" +
                  ("\n🛠️ Администрирование" if is_admin else ""),
            inline=False
        )
        
        # Добавляем поле с инструкцией как получить подробную справку
        main_embed.add_field(
            name="❓ Как пользоваться справкой",
            value="Нажмите на кнопки ниже, чтобы получить информацию по конкретной категории команд.",
            inline=False
        )
        
        # Добавляем футер
        main_embed.set_footer(text="ВПИ - Военно-Политическая Игра | Версия 1.0")
        
        # Создаем эмбед для раздела Управление страной
        country_embed = discord.Embed(
            title="🗺️ Управление страной",
            description="Команды для выбора и управления вашей страной",
            color=discord.Color.green()
        )
        
        country_embed.add_field(
            name="/select_country [название]",
            value="Выбрать страну для игры. Доступные страны: Украина, Россия, Беларусь.",
            inline=False
        )
        
        country_embed.add_field(
            name="/my_country",
            value="Показать подробную информацию о вашей стране, включая политическую систему, экономику и военную статистику.",
            inline=False
        )
        
        country_embed.add_field(
            name="/set_political_system",
            value="Выбрать политическую систему для вашей страны. Каждая система дает уникальные бонусы и штрафы.",
            inline=False
        )
        
        country_embed.add_field(
            name="/political_systems",
            value="Показать информацию о всех доступных политических системах и их эффектах.",
            inline=False
        )
        
        # Создаем эмбед для раздела Экономика
        economy_embed = discord.Embed(
            title="💰 Экономика",
            description="Команды для управления бюджетом и ресурсами",
            color=discord.Color.gold()
        )
        
        economy_embed.add_field(
            name="/inventory",
            value="Показать ваш инвентарь, бюджет и военные силы.",
            inline=False
        )
        
        economy_embed.add_field(
            name="/buy",
            value="Открыть меню покупки военной техники.",
            inline=False
        )
        
        economy_embed.add_field(
            name="/build_factory",
            value=f"Построить военный завод за 100,000$. Производит 1,000 боеприпасов в час.",
            inline=False
        )
        
        economy_embed.add_field(
            name="/factories",
            value="Управление заводами пехотного вооружения и сбор произведенного пехотного вооружения.",
            inline=False
        )
        
        # Создаем эмбед для раздела Военная техника
        military_embed = discord.Embed(
            title="🛒 Военная техника",
            description="Команды для покупки различных типов военной техники",
            color=discord.Color.red()
        )
        
        # Создаем таблицу с информацией о военной технике
        for unit_type, info in UNITS_INFO.items():
            military_embed.add_field(
                name=f"{info['name']} | `/buy_{unit_type} [кол-во]`",
                value=f"Цена: {info['cost']:,}$\n"
                      f"Пехотное вооружение: {info['ammo']} на единицу\n"
                      f"Боевая мощь: {info['power']}",
                inline=True
            )
        
        # Создаем эмбед для раздела Военные действия
        battle_embed = discord.Embed(
            title="⚔️ Военные действия",
            description="Команды для ведения боевых действий",
            color=discord.Color.dark_red()
        )
        
        battle_embed.add_field(
            name="/attack @игрок",
            value="Атаковать другого игрока всеми вашими силами.\n"
                  "Победитель определяется на основе боевой мощи с учетом случайного фактора (±20%).\n"
                  "Проигравший теряет все войска, победитель - 30% войск.",
            inline=False
        )
        
        battle_embed.add_field(
            name="/history",
            value="Показать историю ваших боев.",
            inline=False
        )
        
        # Создаем эмбед для раздела Администрирование (только для админов)
        admin_embed = None
        if is_admin:
            admin_embed = discord.Embed(
                title="🛠️ Администрирование",
                description="Команды доступные только администраторам",
                color=discord.Color.dark_purple()
            )
            
            admin_embed.add_field(
                name="/admin_help",
                value="Показать подробную справку по административным командам.",
                inline=False
            )
            
            admin_embed.add_field(
                name="/grant_money @игрок сумма",
                value="Выдать указанную сумму денег игроку.",
                inline=False
            )
            
            admin_embed.add_field(
                name="/set_money @игрок сумма",
                value="Установить определенную сумму денег игроку.",
                inline=False
            )
            
            admin_embed.add_field(
                name="/grant_ammo @игрок количество",
                value="Выдать указанное количество пехотного вооружения игроку",
                inline=False
            )
            
            admin_embed.add_field(
                name="/set_country @игрок страна",
                value="Назначить страну игроку.",
                inline=False
            )
            
            admin_embed.add_field(
                name="/reset_country @игрок",
                value="Сбросить страну игрока.",
                inline=False
            )
            
            admin_embed.add_field(
                name="/admin_set_political_system @игрок [система]",
                value="Установить политическую систему игроку.",
                inline=False
            )
        
        # Создаем кнопки навигации
        buttons = []
        
        class HelpView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=120)  # 2 минуты таймаут
                self.message = None
            
            @discord.ui.button(label="🗺️ Страны", style=discord.ButtonStyle.green, custom_id="country")
            async def country_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("Эта кнопка не для вас.", ephemeral=True)
                    return
                await interaction.response.edit_message(embed=country_embed, view=self)
            
            @discord.ui.button(label="💰 Экономика", style=discord.ButtonStyle.primary, custom_id="economy")
            async def economy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("Эта кнопка не для вас.", ephemeral=True)
                    return
                await interaction.response.edit_message(embed=economy_embed, view=self)
            
            @discord.ui.button(label="🛒 Техника", style=discord.ButtonStyle.secondary, custom_id="military")
            async def military_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("Эта кнопка не для вас.", ephemeral=True)
                    return
                await interaction.response.edit_message(embed=military_embed, view=self)
            
            @discord.ui.button(label="⚔️ Война", style=discord.ButtonStyle.danger, custom_id="battle")
            async def battle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("Эта кнопка не для вас.", ephemeral=True)
                    return
                await interaction.response.edit_message(embed=battle_embed, view=self)
            
            @discord.ui.button(label="🏠 Главная", style=discord.ButtonStyle.success, custom_id="main", row=1)
            async def main_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("Эта кнопка не для вас.", ephemeral=True)
                    return
                await interaction.response.edit_message(embed=main_embed, view=self)
                
            @discord.ui.button(label="❌ Закрыть", style=discord.ButtonStyle.red, custom_id="close", row=1)
            async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("Эта кнопка не для вас.", ephemeral=True)
                    return
                await interaction.message.delete()
                
            async def on_timeout(self):
                # Автоматическое удаление сообщения после истечения таймаута
                if self.message:
                    try:
                        await self.message.delete()
                    except discord.NotFound:
                        # Сообщение уже удалено
                        pass
        
        view = HelpView()
        
        # Добавляем кнопку администратора, если пользователь - админ
        if is_admin:
            # Поскольку мы не можем добавить кнопку напрямую в существующий view,
            # мы создаем новый class AdminHelpView, который наследуется от HelpView
            # и добавляет кнопку администратора
            class AdminHelpView(HelpView):
                @discord.ui.button(label="🛠️ Админ", style=discord.ButtonStyle.primary, custom_id="admin", row=1)
                async def admin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("Эта кнопка не для вас.", ephemeral=True)
                        return
                    await interaction.response.edit_message(embed=admin_embed, view=self)
            
            view = AdminHelpView()
        
        # Отправляем начальное сообщение с главным эмбедом и кнопками
        message = await ctx.send(embed=main_embed, view=view, ephemeral=True)
        view.message = message

async def setup(bot):
    await bot.add_cog(CountryCog(bot)) 