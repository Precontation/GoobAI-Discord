from groq import AsyncGroq
from groq.types.chat import ChatCompletionMessageParam
import discord
import dotenv
import os
import requests
import asyncio

dotenv.load_dotenv()

# Discord stuff
intents = discord.Intents.default()
intents.message_content = True

discord_client = discord.Client(
    intents=intents,
    allowed_mentions=discord.AllowedMentions(
        users=True, roles=False, everyone=False, replied_user=True
    ),
)
tree = discord.app_commands.CommandTree(discord_client)

# Groq AI stuff
groq_client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
system_prompt_url = (
    "https://raw.githubusercontent.com/GoobApp/goobAI-system-prompt/main/prompt.txt"
)
system_prompt = ""

# Custom system prompt
custom_system_prompt = ""
remove_original_system_prompt = False

# Consts
ERROR_MESSAGE = "An error occurred :goob:"
ASSISTANT_MESSAGE_PREFIX = "Goofy Goober: "
OWNER_USER_ID = 766046835109789716
AI_MODEL = "qwen/qwen3.8-27b"
MAX_CONTEXT_MESSAGES = 3

try:
    response = requests.get(system_prompt_url)
    if response.status_code == 200:
        system_prompt = response.text
    else:
        print(f"Failed to retrieve file! Status code: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"An error occurred trying to get the system prompt: {e}")


async def get_ai_message(formatted_messages: list[ChatCompletionMessageParam]):
    try:
        prompt = f"{system_prompt}\nWhen referring to users, use their name without an @ symbol. User messages may be formatted as Username: message. The text before the first colon is the speaker's username and is not part of what they said."

        if remove_original_system_prompt:
            prompt = custom_system_prompt
        elif custom_system_prompt != "":
            prompt += (
                "\n\nIn addition to the system prompt, a custom one was added: "
                + custom_system_prompt
            )

        formatted_prompt: ChatCompletionMessageParam = {
            "role": "system",
            "content": prompt,
        }

        messages: list[ChatCompletionMessageParam] = [
            formatted_prompt
        ] + formatted_messages

        completion = await asyncio.wait_for(
            groq_client.chat.completions.create(
                model=AI_MODEL,
                messages=messages,
                reasoning_effort="none",
                temperature=0.6,
                max_completion_tokens=500,
                top_p=1,
                stream=False,
                stop=None,
            ),
            timeout=25,
        )
    except Exception as e:
        print(f"Groq failed! Error: {e}")
        return ERROR_MESSAGE

    if len(completion.choices) != 0 and completion.choices[0].message.content:
        return completion.choices[0].message.content
    else:
        return ERROR_MESSAGE


@discord_client.event
async def on_ready():
    await tree.sync()
    print(f"Bot is logged in and ready!")


@discord_client.event
async def on_message(message: discord.Message):
    if not (
        (discord_client.user in message.mentions or message.guild is None)
        and message.author != discord_client.user
    ):
        return

    async with message.channel.typing():
        messages: list[discord.Message] = []
        messages = [
            m async for m in message.channel.history(limit=MAX_CONTEXT_MESSAGES)
        ]
        messages.reverse()  # Reverse it to make it chronological now

        formattedMessages: list[ChatCompletionMessageParam] = []

        for m in messages:
            content = m.author.display_name + ": " + m.clean_content
            if m.author == discord_client.user:
                if m.clean_content == ERROR_MESSAGE:
                    continue  # Don't have it knowing it errored!

                formattedMessages.append(
                    {
                        "role": "assistant",
                        "content": content.removeprefix(
                            ASSISTANT_MESSAGE_PREFIX
                        ),  # Remove so the AI doesn't bug out and go insane
                    }
                )
            else:
                img = None
                if m.attachments and message.id == m.id:
                    # If there's an attached image, take the first one as context.
                    # But only if it's the current message because it can burn tokens fast.
                    for attachment in m.attachments:
                        if (
                            attachment.content_type
                            and attachment.content_type.startswith("image/")
                        ):
                            img = attachment.url
                            break

                if img:
                    formattedMessages.append(
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": content},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": img},
                                },
                            ],
                        }
                    )
                else:
                    formattedMessages.append({"role": "user", "content": content})

        message_response = await get_ai_message(formattedMessages)
        await message.reply(message_response)


@tree.command(name="ask", description="Ask Goofy Goober a question")
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.allowed_installs(guilds=True, users=True)
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer()

    message_response = await get_ai_message([{"role": "user", "content": question}])

    await interaction.followup.send(
        f"{interaction.user.display_name}: {question}\n{ASSISTANT_MESSAGE_PREFIX}{message_response}"
    )


@tree.command(
    name="set_prompt", description="YOU DONT GET TO USE ONLY I DO ASKDLFJALSDKJF"
)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.allowed_installs(guilds=True, users=True)
async def set_prompt(
    interaction: discord.Interaction, prompt: str = "", replace_original: bool = False
):
    global custom_system_prompt
    global remove_original_system_prompt

    if interaction.user.id != OWNER_USER_ID:
        await interaction.response.send_message(
            f"nuh uh you no dont use", ephemeral=True
        )
        return

    custom_system_prompt = prompt
    remove_original_system_prompt = replace_original

    await interaction.response.send_message(
        f"k set :goob: 🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪🫪",
        ephemeral=True,
    )


discord_client.run(os.environ["DISCORD_BOT_TOKEN"])
