import discord
from discord.ext import commands
import logging
from utils.db import (check_has_country, create_player, get_player_country, 
                     get_player_political_system, set_player_political_system,
                     get_player_data)
from config.political_systems import (POLITICAL_SYSTEMS, get_political_system_info, 
                                     get_political_system_name, format_effect)

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

class PoliticalSystemSelectView(CloseView):
    def __init__(self, ctx, callback):
        super().__init__(ctx)
        self.callback = callback
        
        # Добавляем кнопки для выбора политической системы
        for sys_id, sys_info in POLITICAL_SYSTEMS.items():
            self.add_item(PoliticalSystemButton(
                sys_id,
                f"{sys_info['emoji']} {sys_info['name']}",
                sys_info.get('description', ''),
                row=0 if len(self.children) < 5 else 1
            ))
    
    async def handle_select(self, interaction, system_id):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Эта кнопка не для вас.", ephemeral=True)
            return
            
        await self.callback(interaction, system_id)

class PoliticalSystemButton(discord.ui.Button):
    def __init__(self, system_id, label, description, row=0):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=label,
            custom_id=f"polsys_{system_id}",
            row=row
        )
        self.system_id = system_id
        self.description = description
    
    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if isinstance(view, PoliticalSystemSelectView):
            await view.handle_select(interaction, self.system_id)

class PoliticsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def is_admin(self, ctx):
        """Проверка, является ли пользователь администратором"""
        return ctx.author.name.lower() in [name.lower() for name in ADMIN_USERNAMES]
    
    @commands.command(name='political_systems')
    async def show_political_systems(self, ctx):
        """Показать информацию о всех политических системах"""
        embed = discord.Embed(
            title="📜 Политические системы",
            description="Информация о доступных политических системах и их эффектах:",
            color=discord.Color.gold()
        )
        
        for sys_id, sys_info in POLITICAL_SYSTEMS.items():
            # Формируем список эффектов
            effects = []
            for effect_key, effect_value in sys_info['effects'].items():
                if effect_key == 'production_bonus' or effect_key == 'production_penalty':
                    effects.append(f"Производство пехотного вооружения: {format_effect(effect_value)}")
                elif effect_key == 'economy_bonus' or effect_key == 'economy_penalty':
                    effects.append(f"Экономика: {format_effect(effect_value)}")
                elif effect_key == 'military_bonus' or effect_key == 'military_penalty':
                    effects.append(f"Боевая мощь: {format_effect(effect_value)}")
            
            effects_text = "\n".join(effects) if effects else "Нет эффектов"
            
            # Добавляем поле для каждой системы
            embed.add_field(
                name=f"{sys_info['emoji']} {sys_info['name']}",
                value=f"{sys_info['description']}\n\n**Эффекты:**\n{effects_text}",
                inline=False
            )
        
        # Добавляем примечание о смене политической системы
        embed.add_field(
            name="📝 Примечание",
            value="Политическая система вашей страны не может быть изменена самостоятельно. "
                  "Смена политической системы - это результат внутриполитических процессов, "
                  "которые могут произойти во время игровых событий.",
            inline=False
        )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
    
    @commands.command(name='admin_set_political_system')
    async def admin_set_political_system(self, ctx, target: discord.Member, system_id: str = None):
        """[ADMIN] Установить политическую систему игроку"""
        # Проверяем, является ли пользователь администратором
        if not await self.is_admin(ctx):
            await ctx.send("У вас нет прав для использования этой команды.", ephemeral=True)
            return
        
        # Проверяем, выбрана ли страна
        if not check_has_country(target.id):
            await ctx.send(f"У {target.name} не выбрана страна.", ephemeral=True)
            return
        
        country = get_player_country(target.id)
        
        # Если system_id не указан, показываем текущую систему и список доступных
        if not system_id:
            current_system = get_player_political_system(target.id)
            
            embed = discord.Embed(
                title=f"Политическая система | {target.name} | {country}",
                description=f"Текущая политическая система: **{get_political_system_name(current_system) if current_system else 'Не выбрана'}**\n\n"
                           f"Для установки новой системы, используйте команду:\n"
                           f"`/admin_set_political_system @{target.name} [ID системы]`",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Доступные политические системы:",
                value="\n".join([f"• `{sys_id}` - {sys_info['emoji']} {sys_info['name']}" for sys_id, sys_info in POLITICAL_SYSTEMS.items()]),
                inline=False
            )
            
            view = CloseView(ctx)
            message = await ctx.send(embed=embed, view=view)
            view.message = message
            return
        
        # Проверяем корректность system_id
        if system_id not in POLITICAL_SYSTEMS:
            available_systems = ", ".join([f"`{sys_id}`" for sys_id in POLITICAL_SYSTEMS.keys()])
            await ctx.send(f"Некорректный ID политической системы. Доступные варианты: {available_systems}", ephemeral=True)
            return
        
        # Устанавливаем политическую систему
        set_player_political_system(target.id, system_id)
        
        system_info = get_political_system_info(system_id)
        
        embed = discord.Embed(
            title=f"Политическая система установлена | {target.name} | {country}",
            description=f"Администратор {ctx.author.name} установил политическую систему: {system_info['emoji']} **{system_info['name']}**\n\n"
                       f"*{system_info['description']}*",
            color=discord.Color.green()
        )
        
        # Добавляем эффекты системы
        effects_text = ""
        for effect_key, effect_value in system_info['effects'].items():
            if 'production' in effect_key:
                effects_text += f"Производство пехотного вооружения: {format_effect(effect_value)}\n"
            elif 'economy' in effect_key:
                effects_text += f"Экономика: {format_effect(effect_value)}\n"
            elif 'military' in effect_key:
                effects_text += f"Боевая мощь: {format_effect(effect_value)}\n"
        
        embed.add_field(
            name="Эффекты",
            value=effects_text or "Нет эффектов",
            inline=False
        )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view)
        view.message = message
        
        # Отправляем уведомление игроку
        try:
            player_embed = discord.Embed(
                title=f"🏛️ Политическая система изменена!",
                description=f"Администратор {ctx.author.name} установил политическую систему вашей страны: {system_info['emoji']} **{system_info['name']}**\n\n"
                           f"*{system_info['description']}*",
                color=discord.Color.blue()
            )
            
            player_embed.add_field(
                name="Эффекты",
                value=effects_text or "Нет эффектов",
                inline=False
            )
            
            player_view = CloseView(ctx)
            player_message = await target.send(embed=player_embed, view=player_view)
            player_view.message = player_message
        except discord.Forbidden:
            await ctx.send(f"Не удалось отправить уведомление игроку {target.name} (личные сообщения закрыты)")

async def setup(bot):
    await bot.add_cog(PoliticsCog(bot)) 