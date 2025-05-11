import discord
from discord.ext import commands
import logging
from utils.db import (check_has_country, get_player_country, get_player_regions,
                     get_player_controlled_regions, get_region_control_status,
                     change_region_control, set_region_damage, repair_region,
                     get_adjusted_economic_bonus, get_player_data)
from config.regions import (COUNTRY_REGIONS, get_region_info, get_region_name,
                          get_region_effects, format_effect, get_region_emoji_and_name)

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

class RegionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_admin(self, ctx):
        """Проверка, является ли пользователь администратором"""
        return ctx.author.name.lower() in [name.lower() for name in ADMIN_USERNAMES]
    
    @commands.command(name='regions')
    async def show_regions(self, ctx):
        """Показать информацию о регионах игрока"""
        # Проверяем, выбрал ли игрок страну
        if not check_has_country(ctx.author.id):
            await ctx.send("Сначала выберите страну командой `/select_country`", ephemeral=True)
            return
        
        country = get_player_country(ctx.author.id)
        regions = get_player_regions(ctx.author.id)
        
        if not regions:
            await ctx.send(f"У вас нет контролируемых регионов в стране {country}.", ephemeral=True)
            return
        
        # Получаем детальную информацию о регионах
        regions_details = get_player_controlled_regions(ctx.author.id)
        
        # Формируем эмбед с информацией
        embed = discord.Embed(
            title=f"Регионы страны {country}",
            description=f"У вас {len(regions)} контролируемых регионов",
            color=discord.Color.blue()
        )
        
        # Группируем регионы по категориям
        normal_regions = []
        damaged_regions = []
        
        for region_id, is_damaged, damage_level in regions_details:
            region_info = get_region_info(country, region_id)
            if not region_info:
                continue
                
            region_text = f"{region_info['emoji']} **{region_info['name']}**\n"
            region_text += f"_{region_info['description']}_\n"
            
            # Добавляем эффекты региона
            effects_text = []
            for effect_key, effect_value in region_info['effects'].items():
                if 'production' in effect_key:
                    effects_text.append(f"Производство: {format_effect(effect_value)}")
                elif 'economy' in effect_key:
                    effects_text.append(f"Экономика: {format_effect(effect_value)}")
                elif 'military' in effect_key:
                    effects_text.append(f"Военная мощь: {format_effect(effect_value)}")
            
            if effects_text:
                region_text += "Эффекты: " + ", ".join(effects_text) + "\n"
                
            # Добавляем информацию о повреждениях
            if is_damaged:
                damage_percent = int(damage_level * 25)
                region_text += f"⚠️ **Регион поврежден** (уровень {damage_level}/4, -{damage_percent}% к эффективности)\n"
                damaged_regions.append(region_text)
            else:
                normal_regions.append(region_text)
        
        # Добавляем информацию о регионах в эмбед
        if normal_regions:
            embed.add_field(
                name="🟢 Нормальные регионы",
                value="\n".join(normal_regions),
                inline=False
            )
        
        if damaged_regions:
            embed.add_field(
                name="🔴 Поврежденные регионы",
                value="\n".join(damaged_regions),
                inline=False
            )
        
        # Общие бонусы от всех регионов
        econ_bonus = get_adjusted_economic_bonus(ctx.author.id)
        embed.add_field(
            name="📊 Общий бонус от всех регионов и политической системы",
            value=f"Экономика: {format_effect(econ_bonus)}",
            inline=False
        )
        
        # Отправляем сообщение
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
    
    @commands.command(name='view_region')
    async def view_region(self, ctx, region_id: str = None):
        """Просмотреть детальную информацию о регионе"""
        # Проверяем, выбрал ли игрок страну
        if not check_has_country(ctx.author.id):
            await ctx.send("Сначала выберите страну командой `/select_country`", ephemeral=True)
            return
        
        country = get_player_country(ctx.author.id)
        
        # Если регион не указан, показываем список доступных регионов
        if not region_id:
            regions = get_player_regions(ctx.author.id)
            if not regions:
                await ctx.send(f"У вас нет контролируемых регионов в стране {country}.", ephemeral=True)
                return
            
            available_regions = []
            for r_id in regions:
                region_info = get_region_info(country, r_id)
                if region_info:
                    available_regions.append(f"`{r_id}` - {region_info['emoji']} {region_info['name']}")
            
            embed = discord.Embed(
                title=f"Доступные регионы страны {country}",
                description="Используйте команду `/view_region [id_региона]` для просмотра детальной информации",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Ваши регионы",
                value="\n".join(available_regions) if available_regions else "Нет регионов",
                inline=False
            )
            
            view = CloseView(ctx)
            message = await ctx.send(embed=embed, view=view)
            view.message = message
            return
        
        # Проверяем, существует ли такой регион для данной страны
        region_info = get_region_info(country, region_id)
        if not region_info:
            await ctx.send(f"Регион с ID '{region_id}' не найден для страны {country}.", ephemeral=True)
            return
        
        # Проверяем, контролирует ли игрок этот регион
        region_status = get_region_control_status(ctx.author.id, region_id)
        if not region_status or not region_status['is_controlled']:
            await ctx.send(f"Вы не контролируете регион {region_info['name']}.", ephemeral=True)
            return
        
        # Формируем эмбед с детальной информацией о регионе
        embed = discord.Embed(
            title=f"{region_info['emoji']} {region_info['name']}",
            description=region_info['description'],
            color=discord.Color.gold()
        )
        
        # Основная информация
        embed.add_field(
            name="📍 Основная информация",
            value=f"**Столица:** {region_info['capital']}\n"
                  f"**Страна:** {country}\n"
                  f"**ID региона:** `{region_id}`",
            inline=False
        )
        
        # Эффекты региона
        effects_text = []
        for effect_key, effect_value in region_info['effects'].items():
            if 'production' in effect_key:
                effects_text.append(f"Производство: {format_effect(effect_value)}")
            elif 'economy' in effect_key:
                effects_text.append(f"Экономика: {format_effect(effect_value)}")
            elif 'military' in effect_key:
                effects_text.append(f"Военная мощь: {format_effect(effect_value)}")
        
        embed.add_field(
            name="🔄 Эффекты",
            value="\n".join(effects_text) if effects_text else "Нет эффектов",
            inline=False
        )
        
        # Статус региона
        status_text = "🟢 **Нормальное состояние**"
        if region_status['is_damaged']:
            damage_level = region_status['damage_level']
            damage_percent = int(damage_level * 25)
            status_text = f"🔴 **Регион поврежден**\n"
            status_text += f"Уровень повреждения: {damage_level}/4\n"
            status_text += f"Снижение эффективности: -{damage_percent}%"
        
        embed.add_field(
            name="⚙️ Текущий статус",
            value=status_text,
            inline=False
        )
        
        # Отправляем сообщение
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
    
    @commands.command(name='admin_region_control')
    async def admin_region_control(self, ctx, target: discord.Member, region_id: str, control: str = "gain"):
        """[ADMIN] Изменяет контроль игрока над регионом (gain/lose)"""
        # Проверяем, является ли пользователь администратором
        if not await self.is_admin(ctx):
            await ctx.send("У вас нет прав для использования этой команды.", ephemeral=True)
            return
        
        # Проверяем, выбрана ли страна у целевого игрока
        if not check_has_country(target.id):
            await ctx.send(f"У {target.name} не выбрана страна.", ephemeral=True)
            return
        
        country = get_player_country(target.id)
        
        # Проверяем, существует ли такой регион для данной страны
        region_info = get_region_info(country, region_id)
        if not region_info:
            await ctx.send(f"Регион с ID '{region_id}' не найден для страны {country}.", ephemeral=True)
            return
        
        # Проверяем правильность параметра control
        is_gain = control.lower() == "gain"
        if not is_gain and control.lower() != "lose":
            await ctx.send("Параметр control должен быть 'gain' или 'lose'.", ephemeral=True)
            return
        
        # Изменяем контроль над регионом
        result = change_region_control(target.id, region_id, is_controlled=is_gain)
        
        if not result:
            await ctx.send(f"Не удалось изменить контроль над регионом {region_info['name']}.", ephemeral=True)
            return
        
        # Формируем сообщение об успешном изменении
        action_text = "получил контроль над" if is_gain else "потерял контроль над"
        
        embed = discord.Embed(
            title=f"Изменение контроля над регионом",
            description=f"Игрок {target.name} {action_text} регионом {region_info['emoji']} **{region_info['name']}**",
            color=discord.Color.green() if is_gain else discord.Color.red()
        )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
        
        # Отправляем уведомление игроку
        try:
            player_embed = discord.Embed(
                title=f"{'🟢' if is_gain else '🔴'} Изменение контроля над регионом",
                description=f"Вы {action_text} регионом {region_info['emoji']} **{region_info['name']}**\n\n"
                           f"*{region_info['description']}*",
                color=discord.Color.green() if is_gain else discord.Color.red()
            )
            
            # Добавляем информацию об эффектах, если регион был получен
            if is_gain:
                effects_text = []
                for effect_key, effect_value in region_info['effects'].items():
                    if 'production' in effect_key:
                        effects_text.append(f"Производство: {format_effect(effect_value)}")
                    elif 'economy' in effect_key:
                        effects_text.append(f"Экономика: {format_effect(effect_value)}")
                    elif 'military' in effect_key:
                        effects_text.append(f"Военная мощь: {format_effect(effect_value)}")
                
                if effects_text:
                    player_embed.add_field(
                        name="🔄 Эффекты",
                        value="\n".join(effects_text),
                        inline=False
                    )
            
            player_view = CloseView(ctx)
            player_message = await target.send(embed=player_embed, view=player_view)
            player_view.message = player_message
        except discord.Forbidden:
            await ctx.send(f"Не удалось отправить уведомление игроку {target.name} (личные сообщения закрыты)")
    
    @commands.command(name='admin_damage_region')
    async def admin_damage_region(self, ctx, target: discord.Member, region_id: str, damage_level: int = 1):
        """[ADMIN] Устанавливает уровень повреждения региона (0-4)"""
        # Проверяем, является ли пользователь администратором
        if not await self.is_admin(ctx):
            await ctx.send("У вас нет прав для использования этой команды.", ephemeral=True)
            return
        
        # Проверяем, выбрана ли страна у целевого игрока
        if not check_has_country(target.id):
            await ctx.send(f"У {target.name} не выбрана страна.", ephemeral=True)
            return
        
        country = get_player_country(target.id)
        
        # Проверяем, существует ли такой регион для данной страны
        region_info = get_region_info(country, region_id)
        if not region_info:
            await ctx.send(f"Регион с ID '{region_id}' не найден для страны {country}.", ephemeral=True)
            return
        
        # Проверяем, контролирует ли игрок этот регион
        region_status = get_region_control_status(target.id, region_id)
        if not region_status or not region_status['is_controlled']:
            await ctx.send(f"Игрок {target.name} не контролирует регион {region_info['name']}.", ephemeral=True)
            return
        
        # Проверяем корректность уровня повреждения
        if damage_level < 0 or damage_level > 4:
            await ctx.send("Уровень повреждения должен быть от 0 до 4.", ephemeral=True)
            return
        
        # Устанавливаем уровень повреждения
        is_damaged = damage_level > 0
        result = set_region_damage(target.id, region_id, is_damaged, damage_level)
        
        if not result:
            await ctx.send(f"Не удалось изменить статус повреждения региона {region_info['name']}.", ephemeral=True)
            return
        
        # Формируем сообщение об успешном изменении
        action_text = "поврежден" if is_damaged else "восстановлен"
        
        embed = discord.Embed(
            title=f"Изменение статуса региона",
            description=f"Регион {region_info['emoji']} **{region_info['name']}** {action_text}",
            color=discord.Color.red() if is_damaged else discord.Color.green()
        )
        
        if is_damaged:
            damage_percent = damage_level * 25
            embed.add_field(
                name="📊 Информация о повреждении",
                value=f"Уровень повреждения: {damage_level}/4\n"
                      f"Снижение эффективности: -{damage_percent}%",
                inline=False
            )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
        
        # Отправляем уведомление игроку
        try:
            player_embed = discord.Embed(
                title=f"{'🔴' if is_damaged else '🟢'} Изменение статуса региона",
                description=f"Ваш регион {region_info['emoji']} **{region_info['name']}** {action_text}\n\n"
                           f"*{region_info['description']}*",
                color=discord.Color.red() if is_damaged else discord.Color.green()
            )
            
            if is_damaged:
                damage_percent = damage_level * 25
                player_embed.add_field(
                    name="📊 Информация о повреждении",
                    value=f"Уровень повреждения: {damage_level}/4\n"
                          f"Снижение эффективности: -{damage_percent}%\n\n"
                          f"⚠️ Эффективность всех бонусов региона снижена.",
                    inline=False
                )
            else:
                player_embed.add_field(
                    name="📊 Информация о восстановлении",
                    value=f"Регион полностью восстановлен и функционирует на 100% эффективности.",
                    inline=False
                )
            
            player_view = CloseView(ctx)
            player_message = await target.send(embed=player_embed, view=player_view)
            player_view.message = player_message
        except discord.Forbidden:
            await ctx.send(f"Не удалось отправить уведомление игроку {target.name} (личные сообщения закрыты)")

    @commands.command(name='country_regions')
    async def show_country_regions(self, ctx, country_name: str = None):
        """Показать список всех регионов для указанной страны"""
        # Если страна не указана, используем страну игрока
        if not country_name:
            if not check_has_country(ctx.author.id):
                await ctx.send("Укажите название страны или выберите свою страну командой `/select_country`", ephemeral=True)
                return
            country_name = get_player_country(ctx.author.id)
        
        # Проверяем, есть ли регионы для указанной страны
        if country_name not in COUNTRY_REGIONS:
            await ctx.send(f"Для страны '{country_name}' не найдено регионов.", ephemeral=True)
            return
        
        regions = COUNTRY_REGIONS[country_name]
        
        # Группируем регионы по типу (основные, столичные и т.д.)
        capital_regions = []
        strategic_regions = []
        normal_regions = []
        
        for region_id, region_info in regions.items():
            region_text = f"`{region_id}` - {region_info['emoji']} **{region_info['name']}**"
            
            if region_info.get('is_capital', False):
                capital_regions.append(region_text)
            elif any(effect_value >= 0.1 for effect_key, effect_value in region_info['effects'].items()):
                strategic_regions.append(region_text)
            else:
                normal_regions.append(region_text)
        
        # Формируем эмбед
        embed = discord.Embed(
            title=f"Регионы страны {country_name}",
            description=f"Всего регионов: {len(regions)}",
            color=discord.Color.blue()
        )
        
        if capital_regions:
            embed.add_field(
                name="🏛️ Столичные регионы",
                value="\n".join(capital_regions),
                inline=False
            )
        
        if strategic_regions:
            embed.add_field(
                name="⭐ Стратегические регионы",
                value="\n".join(strategic_regions),
                inline=False
            )
        
        if normal_regions:
            embed.add_field(
                name="🔹 Обычные регионы",
                value="\n".join(normal_regions),
                inline=False
            )
        
        embed.add_field(
            name="ℹ️ Использование",
            value="Для просмотра детальной информации о регионе, используйте команду `/view_region [id_региона]`",
            inline=False
        )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

async def setup(bot):
    await bot.add_cog(RegionCog(bot)) 