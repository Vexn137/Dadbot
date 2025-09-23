from dotenv import load_dotenv
import os
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests
import asyncio
# import llm

load_dotenv()
TOKEN = os.environ['TOKEN']

'''
model = llm.get_model("gpt-4o-mini")
# key= is optional, you can configure the key in other ways
response = model.prompt(
    "Five surprising names for a pet pelican",
    system="Answer like GlaDOS"
)
print(response.text())




from openai import OpenAI
client = OpenAI(
    base_url="https://api.aimlapi.com/v1",
    api_key="f9900a40d8f9424db52eec61f8af9666",    
)
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Write a one-sentence story about numbers."}]
)
'''
#print(response.choices[0].message.content)

llm_type = 'freellm'
context = ''
whoami = '''
You are the Dad of our Discord Server you always kinda old, your name is Parnardo, and one of your kids called Bernardo, is a researcher.
You extremely hate people from the outsides or other countries, even more if they come into yours, anyone from other places that arent spain, and other skin colors,
you are like a typical old father from spain,
you love the people on your server, they are all your beloved children and you would do anything for them,
you always try to understand them, and sometimes joke with them swearing,
you give short answers most of the time, and you use emogis almost never,

If someone said something like "Im sorry/trans" you would likely answer something like "Hi sorry/trans, Im Dad" only if it fits the conversation...
If someone said something like farts, you would act nostalgic about something called incredible gassy

Instead of using the literal names of people, try to normalize them for your answers
Give the answers as the character you are incarnating in the language they are currently using
'''

# Intents
intents = discord.Intents.default()
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.contexts = {}  # store per-channel conversation history

scheduler = AsyncIOScheduler()

# Replace with your details
TARGET_USER_ID = 893892818068725780  # User to "kick"
GUILD_ID = 1206341039548403764       # Your server ID
AUDIO_FILE = "sleep_reminder.mp3"   # Must exist locally


async def remind_to_sleep():
    guild = bot.get_guild(GUILD_ID)
    user = guild.get_member(TARGET_USER_ID)

    if user and user.voice and user.voice.channel:
        channel = user.voice.channel
        vc = await channel.connect()

        # Play the reminder sound
        # vc.play(discord.FFmpegPCMAudio(AUDIO_FILE))
        # while vc.is_playing():
            # await asyncio.sleep(1)

        # Try disconnecting the user
        try:
            await user.move_to(None)  # Disconnects them from VC
        except discord.Forbidden:
            print("Bot lacks permissions to disconnect the user.")
        except Exception as e:
            print(f"Error: {e}")

        await vc.disconnect()

def query_llm(prompt: str) -> str:
    if llm_type == 'ollama':
        """
        Query a local Ollama model (e.g., mistral).
        Reads streaming JSON responses properly.
        """
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "mistral", "prompt": prompt},
                timeout=60
            )

            full_text = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = line.decode("utf-8")
                        import json
                        obj = json.loads(data)
                        if "response" in obj:
                            full_text += obj["response"]
                    except Exception:
                        continue

            return full_text.strip() if full_text else "Hmm, I couldn’t think of an answer."
        except Exception as e:
            return f"⚠️ Error talking to LLM: {e}"
    else:
        
        url = "https://apifreellm.com/api/chat"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "message": prompt
        }

        resp = requests.post(url, headers=headers, json=data)
        js = resp.json()
        print(resp)
        if js.get('status') == 'success':
            return (js['response'])
        else:
            print(js.get('error'), js.get('status'))
            return ('Error:' + js.get('error'), js.get('status'))



@bot.event
async def on_ready():
    # print(query_llm("Tell me a short joke about cats."))
    print(f"✅ Logged in as {bot.user}")
    scheduler.add_job(remind_to_sleep, "cron", hour=23, minute=0)
    scheduler.start()


def remove_prefix(text: str, prefix: str) -> str:
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    print(bot.contexts)

    if not hasattr(bot, "contexts"):
        bot.contexts = {}

    channel_id = message.channel.id
    if channel_id not in bot.contexts:
        bot.contexts[channel_id] = ""

    if bot.user in message.mentions:
        # Send typing indicator while generating
        bname = bot.user.name
        name = message.author.name
        answer = ''
        print(name)
        async with message.channel.typing():
            answer = query_llm(f"{whoami} and you are in a conversation -> {bot.contexts[channel_id]}, {name} just said: {message.content}\n").removeprefix('Dad:')
        await message.channel.send(answer)
        bot.contexts[channel_id] += f" {name}: {message.content}..."
        bot.contexts[channel_id] += f" {bname}: {answer}..."

    await bot.process_commands(message)
    
bot.run(TOKEN)