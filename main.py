from groq import AsyncGroq
import discord
from discord.ext import commands
import dotenv
import os
import requests

dotenv.load_dotenv()

# Discord stuff
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Groq AI stuff
client = AsyncGroq(api_key=os.environ['GROQ_API_KEY'])
system_prompt_url = 'https://ai.goobapp.org/prompt.txt'
system_prompt = ''

try:
    response = requests.get(system_prompt_url) # TODO: check for new system prompt every bot message, so also cache and not return full thing if already most recent
    if response.status_code == 200:
        system_prompt = response.text
    else:
        print(f"Failed to retrieve file! Status code: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Bot is logged in and ready!')

@bot.tree.command(name='ask', description='Ask Goofy Goober a question')
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.allowed_installs(guilds=True, users=True)
async def on_message(interaction: discord.Interaction, question: str):
    await interaction.response.defer()

    completion = await client.chat.completions.create(
        model='moonshotai/kimi-k2-instruct-0905',
        messages=[
        {
            'role': 'system',
            'content': f'{system_prompt}\n\nThe user who messaged you is: {interaction.user.display_name}'
        },
        {
            'role': 'user',
            'content': question
        },
        ],
        temperature=0.6,
        max_completion_tokens=4096,
        top_p=1,
        stream=False,
        stop=None
    )

    await interaction.followup.send(f'{interaction.user.display_name}: {question}\nGoofy Goober: {completion.choices[0].message.content}')


bot.run(str(os.environ['DISCORD_BOT_TOKEN']))


