import os, json, requests
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='w!', intents=intents)

CONFIG_PATH = 'data/config.json'
WEBHOOK_URL = os.getenv('RAILWAY_WEBHOOK', '')  # Optional: For auto-deploy

def load_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except:
        return {"status": {}, "links": {}}

def save_config(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def get_status_color(state):
    colors = {
        'online': 0x00b894,    # Green
        'offline': 0xd63031,   # Red
        'custom': 0xfdcb6e     # Yellow
    }
    return colors.get(state, 0x636e72)

@bot.event
async def on_ready():
    print(f'🤖 Warrior Bot Online: {bot.user}')
    await bot.change_presence(activity=discord.Game(name='w!help for commands'))

# Premium Embed Panel Command
@bot.hybrid_command(name='panel', description='🎛️ Load Server Status Control Panel')
@commands.has_permissions(administrator=True)
async def panel(ctx):
    config = load_config()
    
    embed = discord.Embed(
        title="🎛️ WARRIOR TOOLS - Status Control",
        description="Select a region and status to update the website in real-time!",
        color=0xe17055
    )    
    for region, data in config.get('status', {}).items():
        state_emoji = {'online': '🟢', 'offline': '🔴', 'custom': '🟡'}.get(data['state'], '⚪')
        embed.add_field(
            name=f"{region.upper()} {state_emoji}",
            value=f"Status: `{data['text']}`\nUse `w!status {region} <online|offline|custom> [text]`",
            inline=False
        )
    
    embed.set_footer(text="💡 Example: w!status asia online | w!status europe custom 'Maintenance'")
    
    await ctx.send(embed=embed)

# Status Update Command
@bot.hybrid_command(name='status', description='🔄 Update server status')
@commands.has_permissions(administrator=True)
async def set_status(ctx, region: str, state: str, *, text: str = 'Operational'):
    region = region.lower()
    state = state.lower()
    
    valid_states = ['online', 'offline', 'custom']
    if state not in valid_states:
        await ctx.send(f"❌ Invalid state! Use: {', '.join(valid_states)}", ephemeral=True)
        return
    
    config = load_config()
    if region not in config.get('status', {}):
        await ctx.send(f"❌ Invalid region! Available: {', '.join(config['status'].keys())}", ephemeral=True)
        return
    
    # Update config
    config['status'][region]['state'] = state
    config['status'][region]['text'] = text if state == 'custom' else ('Operational' if state == 'online' else 'Down')
    save_config(config)
    
    # Update website via API (if hosted on same machine or use webhook)
    try:
        # If running locally with Flask
        requests.post('http://localhost:8080/api/update-status', 
                     json={'region': region, 'state': state, 'text': config['status'][region]['text']},
                     timeout=5)
    except:
        pass  # Optional: Use Railway webhook instead
    
    color = get_status_color(state)
    embed = discord.Embed(
        title=f"Status Updated: {region.upper()}",
        description=f"**State:** {state.title()}\n**Text:** `{config['status'][region]['text']}`",
        color=color
    )    await ctx.send(embed=embed)

# Help Command
@bot.hybrid_command(name='help', description='Show available commands')
async def help_cmd(ctx):
    embed = discord.Embed(
        title="WARRIOR TOOLS - Bot Commands",
        description="""
        **Admin Commands:**
        `w!panel` - Load interactive status control panel
        `w!status <region> <state> [text]` - Update server status
        `w!help` - Show this help message
        
        **Regions:** global, asia, europe, americas
        **States:** online (🟢), offline (🔴), custom (🟡)
        
        *Example:* `w!status asia custom 'DDoS Attack - Mitigating'`
        """,
        color=0xe17055
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    await ctx.send(embed=embed)

@panel.error
@set_status.error
async def command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need **Administrator** permission to use this command!", ephemeral=True)

# Run Bot
if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_TOKEN'))
