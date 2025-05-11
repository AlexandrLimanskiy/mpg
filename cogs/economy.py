import discord
from discord.ext import commands
import logging
from utils.db import (get_budget, update_budget, get_inventory, update_inventory, 
                     check_has_country, create_player, get_factories_count, build_factory,
                     calculate_production, get_player_country, get_player_political_system)
from config.config import (FACTORY_COST, FACTORY_PRODUCTION_RATE, UNITS_INFO)
from config.political_systems import get_political_system_info, get_political_system_effects, format_effect

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

class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        """Базовая проверка для всех команд в этом коге"""
        return True  # Все команды доступны по умолчанию
    
    async def is_admin(self, ctx):
        """Проверка, является ли пользователь администратором"""
        return ctx.author.name.lower() in [name.lower() for name in ADMIN_USERNAMES]
    
    @commands.command(name='grant_money')
    async def grant_money(self, ctx, target: discord.Member, amount: int):
        """[ADMIN] Выдать деньги игроку"""
        # Проверяем, является ли пользователь администратором
        if not await self.is_admin(ctx):
            await ctx.send("У вас нет прав для использования этой команды.", ephemeral=True)
            return
        
        if amount <= 0:
            await ctx.send("Сумма должна быть положительным числом!", ephemeral=True)
            return
        
        # Создаем игрока, если его нет в базе
        create_player(target.id, target.name)
        
        # Получаем текущий бюджет и обновляем его
        current_budget = get_budget(target.id)
        new_budget = current_budget + amount
        update_budget(target.id, new_budget)
        
        embed = discord.Embed(
            title="💸 Выдача средств",
            description=f"Администратор {ctx.author.name} выдал {amount:,}$ игроку {target.name}",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Новый баланс игрока",
            value=f"{new_budget:,}$",
            inline=False
        )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
        
        # Отправляем уведомление игроку
        try:
            player_embed = discord.Embed(
                title="💰 Получены средства!",
                description=f"Администратор {ctx.author.name} выдал вам {amount:,}$",
                color=discord.Color.green()
            )
            
            player_embed.add_field(
                name="Ваш новый баланс",
                value=f"{new_budget:,}$",
                inline=False
            )
            
            player_view = CloseView(ctx)
            player_message = await target.send(embed=player_embed, view=player_view)
            player_view.message = player_message
        except discord.Forbidden:
            await ctx.send(f"Не удалось отправить уведомление игроку {target.name} (личные сообщения закрыты)")
    
    @commands.command(name='set_money')
    async def set_money(self, ctx, target: discord.Member, amount: int):
        """[ADMIN] Установить определенную сумму денег игроку"""
        # Проверяем, является ли пользователь администратором
        if not await self.is_admin(ctx):
            await ctx.send("У вас нет прав для использования этой команды.", ephemeral=True)
            return
        
        if amount < 0:
            await ctx.send("Сумма не может быть отрицательной!", ephemeral=True)
            return
        
        # Создаем игрока, если его нет в базе
        create_player(target.id, target.name)
        
        # Устанавливаем новый бюджет
        update_budget(target.id, amount)
        
        embed = discord.Embed(
            title="💰 Установка бюджета",
            description=f"Администратор {ctx.author.name} установил бюджет {amount:,}$ игроку {target.name}",
            color=discord.Color.gold()
        )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
        
        # Отправляем уведомление игроку
        try:
            player_embed = discord.Embed(
                title="💰 Бюджет обновлен!",
                description=f"Администратор {ctx.author.name} установил ваш бюджет на {amount:,}$",
                color=discord.Color.blue()
            )
            
            player_view = CloseView(ctx)
            player_message = await target.send(embed=player_embed, view=player_view)
            player_view.message = player_message
        except discord.Forbidden:
            await ctx.send(f"Не удалось отправить уведомление игроку {target.name} (личные сообщения закрыты)")
    
    @commands.command(name='admin_help')
    async def admin_help(self, ctx):
        """Показать справку по административным командам"""
        # Проверяем, является ли пользователь администратором
        if not await self.is_admin(ctx):
            await ctx.send("У вас нет прав для использования этой команды.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🛠️ Административные команды",
            description="Список доступных админ-команд:",
            color=discord.Color.dark_red()
        )
        
        embed.add_field(
            name="/grant_money @игрок сумма",
            value="Выдать указанную сумму денег игроку",
            inline=False
        )
        
        embed.add_field(
            name="/set_money @игрок сумма",
            value="Установить определенную сумму денег игроку",
            inline=False
        )
        
        embed.add_field(
            name="/grant_ammo @игрок количество",
            value="Выдать указанное количество пехотного вооружения игроку",
            inline=False
        )
        
        embed.add_field(
            name="/set_country @игрок страна",
            value="Назначить страну игроку",
            inline=False
        )
        
        embed.add_field(
            name="/reset_country @игрок",
            value="Сбросить страну игрока",
            inline=False
        )
        
        embed.add_field(
            name="/admin_help",
            value="Показать эту справку",
            inline=False
        )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view, ephemeral=True)
        view.message = message
    
    @commands.command(name='buy')
    async def buy_menu(self, ctx):
        """Открывает меню покупки военной техники"""
        # Проверяем, выбрана ли страна
        if not check_has_country(ctx.author.id):
            await ctx.send("Сначала выберите страну командой `/select_country`", ephemeral=True)
            return
            
        # Создаем игрока, если его нет в базе
        create_player(ctx.author.id, ctx.author.name)
        
        embed = discord.Embed(
            title="Меню покупки военной техники",
            description="Выберите тип техники для покупки",
            color=discord.Color.blue()
        )
        
        # Добавляем информацию обо всех типах юнитов
        for unit_type, info in UNITS_INFO.items():
            embed.add_field(
                name=info['name'],
                value=f"Цена: {info['cost']:,}$\n"
                      f"Требуется пехотного вооружения: {info['ammo']} на единицу\n"
                      f"Боевая сила: {info['power']}\n"
                      f"Команда для покупки: `/buy_{unit_type} [количество]`",
                inline=False
            )
        
        # Добавляем информацию о заводах
        embed.add_field(
            name="Военный завод пехотного вооружения",
            value=f"Цена: {FACTORY_COST:,}$\n"
                  f"Производство: {FACTORY_PRODUCTION_RATE} единиц пехотного вооружения в час\n"
                  f"Команда для постройки: `/build_factory`",
            inline=False
        )
        
        # Добавляем информацию о текущем бюджете
        budget = get_budget(ctx.author.id)
        embed.add_field(
            name="Ваш бюджет",
            value=f"{budget:,}$",
            inline=False
        )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view, ephemeral=True)
        view.message = message
    
    async def _buy_unit(self, ctx, unit_type, amount):
        """Общая функция для покупки любой военной единицы"""
        if amount < 1:
            await ctx.send("Количество должно быть положительным числом!", ephemeral=True)
            return

        # Проверяем, есть ли такой тип юнита
        if unit_type not in UNITS_INFO:
            await ctx.send(f"Неизвестный тип юнита: {unit_type}", ephemeral=True)
            return

        # Получаем информацию о юните
        unit_info = UNITS_INFO[unit_type]

        # Проверяем, выбрана ли страна
        if not check_has_country(ctx.author.id):
            await ctx.send("Сначала выберите страну командой `/select_country`", ephemeral=True)
            return

        # Проверяем бюджет
        budget = get_budget(ctx.author.id)
        total_cost = amount * unit_info['cost']

        if budget < total_cost:
            await ctx.send(f"Недостаточно средств. Требуется: {total_cost:,}$, у вас: {budget:,}$", ephemeral=True)
            return

        # Проверяем наличие пехотного вооружения
        inventory = get_inventory(ctx.author.id)
        current_ammo = inventory.get('ammo', 0)
        required_ammo = amount * unit_info['ammo']

        if current_ammo < required_ammo:
            await ctx.send(
                f"Недостаточно пехотного вооружения. Требуется: {required_ammo:,}, у вас: {current_ammo:,}",
                ephemeral=True
            )
            return

        # Обновляем бюджет и инвентарь
        update_budget(ctx.author.id, budget - total_cost)
        
        # Обновляем количество юнитов
        current_units = inventory.get(unit_type, 0)
        update_inventory(ctx.author.id, unit_type, current_units + amount)
        
        # Уменьшаем количество пехотного вооружения
        update_inventory(ctx.author.id, 'ammo', current_ammo - required_ammo)

        embed = discord.Embed(
            title=f"Покупка {unit_info['name']}",
            description=f"Куплено {unit_info['name']}: {amount}\n"
                      f"Потрачено денег: {total_cost:,}$\n"
                      f"Использовано пехотного вооружения: {required_ammo:,}",
            color=discord.Color.green()
        )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
    
    @commands.command(name='buy_infantry')
    async def buy_infantry(self, ctx, amount: int = 1):
        """Купить пехоту"""
        await self._buy_unit(ctx, 'infantry', amount)
        
    @commands.command(name='buy_artillery')
    async def buy_artillery(self, ctx, amount: int = 1):
        """Купить артиллерию"""
        await self._buy_unit(ctx, 'artillery', amount)
        
    @commands.command(name='buy_tank')
    async def buy_tank(self, ctx, amount: int = 1):
        """Купить танки"""
        await self._buy_unit(ctx, 'tank', amount)
        
    @commands.command(name='buy_fighter')
    async def buy_fighter(self, ctx, amount: int = 1):
        """Купить истребители"""
        await self._buy_unit(ctx, 'fighter', amount)
        
    @commands.command(name='buy_assault')
    async def buy_assault(self, ctx, amount: int = 1):
        """Купить штурмовики"""
        await self._buy_unit(ctx, 'assault', amount)
        
    @commands.command(name='buy_bomber')
    async def buy_bomber(self, ctx, amount: int = 1):
        """Купить бомбардировщики"""
        await self._buy_unit(ctx, 'bomber', amount)
        
    @commands.command(name='buy_ship')
    async def buy_ship(self, ctx, amount: int = 1):
        """Купить корабли"""
        await self._buy_unit(ctx, 'ship', amount)
    
    @commands.command(name='build_factory')
    async def build_factory_cmd(self, ctx):
        """Построить военный завод"""
        # Проверяем, выбрана ли страна
        if not check_has_country(ctx.author.id):
            await ctx.send("Сначала выберите страну командой `/select_country`", ephemeral=True)
            return

        # Проверяем бюджет
        budget = get_budget(ctx.author.id)
        if budget < FACTORY_COST:
            await ctx.send(f"Недостаточно средств. Требуется: {FACTORY_COST:,}$, у вас: {budget:,}$", ephemeral=True)
            return

        # Строим завод
        build_factory(ctx.author.id)
        update_budget(ctx.author.id, budget - FACTORY_COST)

        factories_count = get_factories_count(ctx.author.id)
        
        embed = discord.Embed(
            title="Военный завод пехотного вооружения построен!",
            description=f"Производство: {FACTORY_PRODUCTION_RATE} единиц пехотного вооружения в час\nВсего заводов: {factories_count}",
            color=discord.Color.green()
        )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
    
    @commands.command(name='factories')
    async def show_factories(self, ctx):
        """Показать информацию о ваших заводах"""
        # Проверяем, выбрана ли страна
        if not check_has_country(ctx.author.id):
            await ctx.send("Сначала выберите страну командой `/select_country`", ephemeral=True)
            return

        factories_count = get_factories_count(ctx.author.id)
        if factories_count == 0:
            await ctx.send("У вас пока нет военных заводов. Используйте команду `/build_factory` для постройки.", ephemeral=True)
            return
            
        production = calculate_production(ctx.author.id)
        
        # Добавляем произведенные единицы пехотного вооружения в инвентарь
        inventory = get_inventory(ctx.author.id)
        current_ammo = inventory.get('ammo', 0)
        update_inventory(ctx.author.id, 'ammo', current_ammo + production)
        
        # Получаем политическую систему для отображения бонусов
        political_system = get_player_political_system(ctx.author.id)
        
        embed = discord.Embed(
            title="Ваши военные заводы пехотного вооружения",
            description=f"Количество заводов: {factories_count}",
            color=discord.Color.blue()
        )
        
        # Базовое производство
        base_production = factories_count * FACTORY_PRODUCTION_RATE
        
        embed.add_field(
            name="Базовое производство",
            value=f"{base_production} единиц пехотного вооружения в час",
            inline=False
        )
        
        # Если есть политическая система, показываем бонус
        if political_system:
            system_info = get_political_system_info(political_system)
            effects = get_political_system_effects(political_system)
            
            production_modifier = 0
            for key, value in effects.items():
                if 'production' in key:
                    production_modifier += value
            
            if production_modifier != 0:
                adjusted_production = int(base_production * (1 + production_modifier))
                
                embed.add_field(
                    name=f"Бонус от политической системы: {system_info['emoji']} {system_info['name']}",
                    value=f"Модификатор: {format_effect(production_modifier)}\n"
                          f"Итоговое производство: {adjusted_production} единиц в час",
                    inline=False
                )
        
        # Произведено с момента последней проверки
        embed.add_field(
            name="Результаты производства",
            value=f"Произведено с последней проверки: {production:,} единиц пехотного вооружения\n"
                  f"Текущий запас: {inventory.get('ammo', 0) + production:,} единиц",
            inline=False
        )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
    
    @commands.command(name='inventory')
    async def show_inventory(self, ctx):
        """Показать инвентарь игрока"""
        if not check_has_country(ctx.author.id):
            await ctx.send("Сначала выберите страну командой `/select_country`", ephemeral=True)
            return

        inventory = get_inventory(ctx.author.id)
        budget = get_budget(ctx.author.id)
        country = get_player_country(ctx.author.id)
        
        embed = discord.Embed(
            title=f"Инвентарь | {ctx.author.name} | {country}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Бюджет",
            value=f"{budget:,}$",
            inline=False
        )
        
        # Добавляем информацию о всех типах юнитов
        for unit_type, info in UNITS_INFO.items():
            unit_count = inventory.get(unit_type, 0)
            if unit_count > 0 or unit_type == 'infantry':  # Всегда показываем пехоту
                embed.add_field(
                    name=info['name'],
                    value=f"{unit_count:,} единиц",
                    inline=True
                )
        
        embed.add_field(
            name="Пехотное вооружение",
            value=f"{inventory.get('ammo', 0):,} единиц",
            inline=True
        )
        
        factories_count = get_factories_count(ctx.author.id)
        if factories_count > 0:
            production_rate = factories_count * FACTORY_PRODUCTION_RATE
            embed.add_field(
                name="Военные заводы пехотного вооружения",
                value=f"{factories_count} (производство: {production_rate} единиц пехотного вооружения/час)",
                inline=True
            )
        
        # Добавляем информацию о боевой мощи
        total_power = 0
        for unit_type, count in inventory.items():
            if unit_type in UNITS_INFO:
                total_power += count * UNITS_INFO[unit_type]['power']
        
        embed.add_field(
            name="Общая боевая мощь",
            value=f"{total_power:,}",
            inline=False
        )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view, ephemeral=True)
        view.message = message

    @commands.command(name='grant_ammo')
    async def grant_ammo(self, ctx, target: discord.Member, amount: int):
        """[ADMIN] Выдать пехотное вооружение игроку"""
        # Проверяем, является ли пользователь администратором
        if not await self.is_admin(ctx):
            await ctx.send("У вас нет прав для использования этой команды.", ephemeral=True)
            return
        
        if amount <= 0:
            await ctx.send("Количество должно быть положительным числом!", ephemeral=True)
            return
        
        # Создаем игрока, если его нет в базе
        create_player(target.id, target.name)
        
        # Получаем текущий инвентарь и обновляем его
        inventory = get_inventory(target.id)
        current_ammo = inventory.get('ammo', 0)
        new_ammo = current_ammo + amount
        update_inventory(target.id, 'ammo', new_ammo)
        
        admin_embed = discord.Embed(
            title=f"✅ Выдано пехотное вооружение",
            description=f"Игроку {target.mention} выдано {amount:,} единиц пехотного вооружения",
            color=discord.Color.green()
        )
        
        admin_embed.add_field(
            name="Текущее пехотное вооружение",
            value=f"{new_ammo:,}",
            inline=False
        )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=admin_embed, view=view)
        view.message = message
        
        # Отправляем уведомление игроку
        try:
            player_embed = discord.Embed(
                title="🧨 Получено пехотное вооружение!",
                description=f"Вы получили {amount:,} единиц пехотного вооружения от администратора {ctx.author.mention}.",
                color=discord.Color.green()
            )
            
            player_embed.add_field(
                name="Текущее пехотное вооружение",
                value=f"{new_ammo:,}",
                inline=False
            )
            
            player_view = CloseView(ctx)
            player_message = await target.send(embed=player_embed, view=player_view)
            player_view.message = player_message
        except discord.Forbidden:
            await ctx.send(f"Не удалось отправить уведомление игроку {target.name} (личные сообщения закрыты)")

async def setup(bot):
    await bot.add_cog(EconomyCog(bot)) 