from groq import AsyncGroq
import discord
from discord.ext import commands
import dotenv
import os
import requests
import asyncio

dotenv.load_dotenv()

# Discord stuff
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Groq AI stuff
client = AsyncGroq(api_key=os.environ['GROQ_API_KEY'])
system_prompt_url = 'https://raw.githubusercontent.com/GoobApp/goobAI-system-prompt/main/prompt.txt'
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

    try:
        completion = await asyncio.wait_for(
            client.chat.completions.create(
                model='qwen/qwen3.6-27b',
                messages=[
                    {
                        'role': 'system',
                        'content': f'{system_prompt}\n\nUser: {interaction.user.display_name}'
                    },
                    {
                        'role': 'user',
                        'content': question
                    },
                ],
                reasoning_effort='none',
                temperature=0.6,
                max_completion_tokens=500,
                top_p=1,
                stream=False,
                stop=None
            ),
            timeout=45
        )
    except asyncio.TimeoutError:
        await interaction.followup.send('Goofy Goober timed out while thinking. Please try again.')
        return
    except Exception as e:
        print(f'Groq request failed: {e}')
        await interaction.followup.send('Goofy Goober hit an error while thinking. Please try again.')
        return

    answer = completion.choices[0].message.content or 'An error occurred. :goob:'
    prefix = f'{interaction.user.display_name}: {question}\nGoofy Goober: '
    message = f'{prefix}{answer}'
    if len(message) > 2000:
        max_answer_len = max(0, 2000 - len(prefix) - len('\n… [truncated]'))
        answer = f'{answer[:max_answer_len]}\n… [truncated]'
        message = f'{prefix}{answer}'

    await interaction.followup.send(message)


bot.run(str(os.environ['DISCORD_BOT_TOKEN']))
