import discord
from discord.ext import commands
import random
import logging
from utils.db import (get_inventory, update_inventory, check_has_country, 
                     create_player, log_battle, get_player_country)
from config.config import UNITS_INFO

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

class BattleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def is_admin(self, ctx):
        """Проверка, является ли пользователь администратором"""
        return ctx.author.name.lower() in [name.lower() for name in ADMIN_USERNAMES]
    
    @commands.command(name='attack')
    async def attack(self, ctx, target: discord.Member):
        """Атака другого игрока"""
        if not check_has_country(ctx.author.id):
            await ctx.send("Сначала выберите страну командой `/select_country`", ephemeral=True)
            return
            
        if not check_has_country(target.id):
            await ctx.send("Ваша цель еще не выбрала страну!", ephemeral=True)
            return
        
        # Создаем игроков, если их нет в базе
        create_player(ctx.author.id, ctx.author.name)
        create_player(target.id, target.name)
        
        # Проверяем, не пытается ли игрок атаковать сам себя
        if target.id == ctx.author.id:
            await ctx.send("Вы не можете атаковать сами себя!", ephemeral=True)
            return
        
        # Получаем инвентари атакующего и защищающегося
        attacker_inventory = get_inventory(ctx.author.id)
        defender_inventory = get_inventory(target.id)
        
        # Проверяем, есть ли у атакующего какие-либо войска
        attacker_has_units = False
        for unit_type in UNITS_INFO:
            if attacker_inventory.get(unit_type, 0) > 0:
                attacker_has_units = True
                break
                
        if not attacker_has_units:
            await ctx.send("У вас нет войск для атаки!", ephemeral=True)
            return
        
        # Создаем эмбед для отчета о битве
        battle_embed = discord.Embed(
            title="⚔️ Боевой отчет ⚔️",
            color=discord.Color.red()
        )
        
        # Добавляем информацию о странах
        attacker_country = get_player_country(ctx.author.id)
        defender_country = get_player_country(target.id)
        
        battle_embed.add_field(
            name="Противостояние",
            value=f"{attacker_country} vs {defender_country}",
            inline=False
        )
        
        # Добавляем информацию о силах сторон
        attacker_forces = ""
        defender_forces = ""
        
        # Рассчитываем общую силу атакующего
        attacker_power = 0
        defender_power = 0
        
        # Подсчитываем силы атакующего
        for unit_type, info in UNITS_INFO.items():
            unit_count = attacker_inventory.get(unit_type, 0)
            if unit_count > 0:
                attacker_forces += f"{info['name']}: {unit_count:,}\n"
                attacker_power += unit_count * info['power']
        
        # Подсчитываем силы защитника
        for unit_type, info in UNITS_INFO.items():
            unit_count = defender_inventory.get(unit_type, 0)
            if unit_count > 0:
                defender_forces += f"{info['name']}: {unit_count:,}\n"
                defender_power += unit_count * info['power']
        
        battle_embed.add_field(
            name=f"Атакующий: {ctx.author.name}",
            value=attacker_forces or "Нет войск",
            inline=True
        )
        
        battle_embed.add_field(
            name=f"Защищающийся: {target.name}",
            value=defender_forces or "Нет войск",
            inline=True
        )
        
        # Добавляем элемент случайности (±20%)
        attacker_random = random.uniform(0.8, 1.2)
        defender_random = random.uniform(0.8, 1.2)
        
        attacker_final = attacker_power * attacker_random
        defender_final = defender_power * defender_random
        
        # Определяем победителя
        # Словари для хранения потерь
        attacker_losses = {}
        defender_losses = {}
        
        if attacker_final > defender_final:
            # Атакующий победил
            # Рассчитываем потери (30% для атакующего, 100% для защитника)
            loss_text = f"Победа {ctx.author.name}!\n\nПотери атакующего:\n"
            
            # Рассчитываем потери атакующего (30%)
            for unit_type, info in UNITS_INFO.items():
                unit_count = attacker_inventory.get(unit_type, 0)
                if unit_count > 0:
                    loss = int(unit_count * 0.3)  # 30% потерь
                    attacker_losses[unit_type] = loss
                    if loss > 0:
                        loss_text += f"{info['name']}: {loss:,}\n"
                        update_inventory(ctx.author.id, unit_type, unit_count - loss)
            
            loss_text += "\nПотери защищающегося:\n"
            
            # Рассчитываем потери защитника (100%)
            for unit_type, info in UNITS_INFO.items():
                unit_count = defender_inventory.get(unit_type, 0)
                if unit_count > 0:
                    defender_losses[unit_type] = unit_count  # 100% потерь
                    loss_text += f"{info['name']}: {unit_count:,}\n"
                    update_inventory(target.id, unit_type, 0)
            
            battle_embed.add_field(
                name="Результат",
                value=loss_text,
                inline=False
            )
            battle_embed.color = discord.Color.green()
            
            # Логируем бой
            log_battle(ctx.author.id, target.id, attacker_power, defender_power,
                     sum(attacker_losses.values()), sum(defender_losses.values()), ctx.author.id)
        else:
            # Защищающийся победил
            # Рассчитываем потери (100% для атакующего, 30% для защитника)
            loss_text = f"Победа {target.name}!\n\nПотери атакующего:\n"
            
            # Рассчитываем потери атакующего (100%)
            for unit_type, info in UNITS_INFO.items():
                unit_count = attacker_inventory.get(unit_type, 0)
                if unit_count > 0:
                    attacker_losses[unit_type] = unit_count  # 100% потерь
                    loss_text += f"{info['name']}: {unit_count:,}\n"
                    update_inventory(ctx.author.id, unit_type, 0)
            
            loss_text += "\nПотери защищающегося:\n"
            
            # Рассчитываем потери защитника (30%)
            for unit_type, info in UNITS_INFO.items():
                unit_count = defender_inventory.get(unit_type, 0)
                if unit_count > 0:
                    loss = int(unit_count * 0.3)  # 30% потерь
                    defender_losses[unit_type] = loss
                    if loss > 0:
                        loss_text += f"{info['name']}: {loss:,}\n"
                        update_inventory(target.id, unit_type, unit_count - loss)
            
            battle_embed.add_field(
                name="Результат",
                value=loss_text,
                inline=False
            )
            battle_embed.color = discord.Color.blue()
            
            # Логируем бой
            log_battle(ctx.author.id, target.id, attacker_power, defender_power,
                     sum(attacker_losses.values()), sum(defender_losses.values()), target.id)
        
        # Отправляем результат боя в канал (публично)
        view = CloseView(ctx)
        message = await ctx.send(embed=battle_embed, view=view)
        view.message = message
        
    @commands.command(name='history')
    async def show_history(self, ctx):
        """Показывает историю боев игрока"""
        from utils.db import get_battle_history

        battles = get_battle_history(ctx.author.id)
        
        if not battles:
            await ctx.send("У вас пока нет истории боев!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"История боев {ctx.author.name}",
            color=discord.Color.purple()
        )
        
        for battle in battles:
            battle_date, attacker, defender, attacker_troops, defender_troops, \
            attacker_losses, defender_losses, winner = battle
            
            battle_info = (
                f"Дата: {battle_date}\n"
                f"Атакующий: {attacker} ({attacker_troops:,} боевая сила)\n"
                f"Защищающийся: {defender} ({defender_troops:,} боевая сила)\n"
                f"Потери атакующего: {attacker_losses:,}\n"
                f"Потери защищающегося: {defender_losses:,}\n"
                f"Победитель: {winner}\n"
            )
            
            embed.add_field(
                name=f"Бой {battle_date}",
                value=battle_info,
                inline=False
            )
        
        view = CloseView(ctx)
        message = await ctx.send(embed=embed, view=view, ephemeral=True)
        view.message = message

async def setup(bot):
    await bot.add_cog(BattleCog(bot)) 