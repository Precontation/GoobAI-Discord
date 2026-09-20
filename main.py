from groq import AsyncGroq
import discord
import dotenv
import os
import requests
import asyncio

dotenv.load_dotenv()

# Discord stuff
intents = discord.Intents.default()
discord_client = discord.Client(intents=intents, 
    allowed_mentions=discord.AllowedMentions(
        users=True,
        roles=False,
        everyone=False,
        replied_user=True
    )
)
tree = discord.app_commands.CommandTree(discord_client)

# Groq AI stuff
groq_client = AsyncGroq(api_key=os.environ['GROQ_API_KEY'])
system_prompt_url = 'https://raw.githubusercontent.com/GoobApp/goobAI-system-prompt/main/prompt.txt'
system_prompt = ''

try:
    response = requests.get(system_prompt_url)
    if response.status_code == 200:
        system_prompt = response.text
    else:
        print(f"Failed to retrieve file! Status code: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

async def get_groq_message(display_name: str, question: str):
    try:
        completion = await asyncio.wait_for(
            groq_client.chat.completions.create(
                model='qwen/qwen3.8-27b',
                messages=[
                {
                    'role': 'system',
                    'content': f'{system_prompt}\nWhen referring to users, use their name without an @ symbol.\n\nUser: {display_name}'
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
                stop=None,
            ),
            timeout=25
        )
    except Exception as e:
        print(f"Groq failed! Error: {e}")
        return "An error occurred :goob:"

    if len(completion.choices) != 0 and completion.choices[0].message.content:
        return completion.choices[0].message.content
    else:
        return "An error occurred :goob:"

@discord_client.event
async def on_ready():
    await tree.sync()
    print(f'Bot is logged in and ready!')

@discord_client.event
async def on_message(message: discord.Message):
    if (discord_client.user in message.mentions or message.guild is None) and message.author != discord_client.user:
        async with message.channel.typing():
            message_response = await get_groq_message(message.author.display_name, message.clean_content)
            await message.reply(message_response)

@tree.command(name='ask', description='Ask Goofy Goober a question')
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.allowed_installs(guilds=True, users=True)
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer()

    message_response = await get_groq_message(interaction.user.display_name, question)

    await interaction.followup.send(f'{interaction.user.display_name}: {question}\nGoofy Goober: {message_response}')


discord_client.run(os.environ['DISCORD_BOT_TOKEN'])