import ai
from ai.types.messages import Message
import discord
import dotenv
import os
import requests

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

# Vercel AI gateway stuff
model = ai.get_model("nvidia/nemotron-nano-9b-v2")
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

try:
    response = requests.get(system_prompt_url)
    if response.status_code == 200:
        system_prompt = response.text
    else:
        print(f"Failed to retrieve file! Status code: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"An error occurred trying to get the system prompt: {e}")


async def get_ai_response(formatted_messages: list[Message]):
    try:
        prompt = f"{system_prompt}\nWhen referring to users, use their name without an @ symbol. User messages may be formatted as Username: message. The text before the first colon is the speaker's username and is not part of what they said."

        if remove_original_system_prompt:
            prompt = custom_system_prompt
        elif custom_system_prompt != "":
            prompt += (
                "\n\nIn addition to the system prompt, a custom one was added: "
                + custom_system_prompt
            )

        prompt += "/no_think"  # Some models use this rather than .with_reasoning_effort("none")

        messages = [ai.system_message(prompt)] + formatted_messages

        async with ai.stream(
            model,
            messages,
            params=ai.InferenceRequestParams(output=ai.OutputParams(max_tokens=500))
            .with_reasoning_effort("none")
            .with_temperature(0.6),
        ) as stream:
            async for event in stream:
                pass

    except Exception as e:
        print(f"AI failed! Error: {e}")
        return ERROR_MESSAGE

    return stream.output


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
        messages = [m async for m in message.channel.history(limit=10)]
        messages.reverse()  # Reverse it to make it chronological now

        formattedMessages: list[Message] = []

        for m in messages:
            content = m.author.display_name + ": " + m.clean_content
            if m.author == discord_client.user:
                if m.clean_content == ERROR_MESSAGE:
                    continue  # Don't have it knowing it errored!
                formattedMessages.append(
                    ai.assistant_message(
                        content.removeprefix(
                            ASSISTANT_MESSAGE_PREFIX
                        ),  # Remove so the AI doesn't bug out and go insane
                    )
                )
            else:
                formattedMessages.append(
                    ai.user_message(
                        content.replace(
                            "\n" + ASSISTANT_MESSAGE_PREFIX, ""
                        )  # If the user did a /ask command don't let the ai freak out
                    )
                )

        message_response = await get_ai_response(formattedMessages)
        await message.reply(message_response)


@tree.command(name="ask", description="Ask Goofy Goober a question")
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.allowed_installs(guilds=True, users=True)
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer()

    message_response = await get_ai_response([ai.user_message(question)])

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
