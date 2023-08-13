# Importings
import discord
import os
import random
import aiohttp
import json
import wolframalpha
import requests
import psycopg2
import youtube_dl

# Importings and loadings
from dotenv import load_dotenv
from discord.ext import commands
from googletrans import Translator
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from youtube import YTDLSource

# Loads the .env file
load_dotenv()

# Grab the dcbot api tokens
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
USER=os.getenv("USER")
PASSWORD=os.getenv("PASSWORD")
DATABASE=os.getenv("DATABASE")
TABLE=os.getenv("TABLE")
SERVER_ID=int(os.getenv("SERVER_ID"))
RECORD=os.getenv("RECORD")
DATABASE_URL=os.getenv("DATABASE_URL")
wolfram_client = wolframalpha.Client('5TEAHK-XKXRAUXUEW') 

# Get all the permissions to dcbot
intents=discord.Intents.default()
intents.message_content=True
intents.presences = True
intents.members = True
intents.guilds=True

#Create an instance of bot
bot = commands.Bot(command_prefix='!',intents=intents)

#quotes=["春风若有怜花意，可否与我再少年","home is where you are","不必太张扬，是花自然香","穷不怪父，丑不怪母，孝不比兄，苦不责妻，气不凶子，一生向阳"]
#Connect with database
#DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@localhost:5432/{DATABASE}"
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()
#Daily quote
async def day_quote():
    #quote=random.choice(quotes)
    #Fetch all informations from motvation
    cur.execute(f"SELECT sentence FROM {TABLE};")
    #Key line of code
    rows = cur.fetchall()
    quotes2=[]
    len=0
    for row in rows:
        quotes2.append(row[0])
        len += 1
    print(len)
    quote=random.choice(quotes2)
    channel=bot.get_channel(1127200981512372264)
    await channel.send(quote)
# dcbot gets activated
@bot.event
async def on_ready():
    # Sends a quote every day at 9:00
    scheduler = AsyncIOScheduler()
    scheduler.add_job(day_quote, CronTrigger(hour="9", minute="0"))
    scheduler.start()
    # Number of how many servers dcbot has connected to
    guild_count = 0
	# Loop through all bots's guilds/server
    for guild in bot.guilds:
        print(f"- {guild.id} (name: {guild.name})")
        guild_count = guild_count + 1

    print("GAP is in " + str(guild_count) + " guilds.")
    
    loop=bot.get_guild(SERVER_ID)
    cur.execute(f"SELECT COUNT(*) FROM {RECORD}")
    rows=cur.fetchone()
    if int(rows[0])==0:
        for member in loop.members:
            temp=member.name
            query=f"INSERT INTO {RECORD} (username) VALUES (%s)"
            cur.execute(query,(temp,))
            conn.commit()
    
#Currently no actual functions
@bot.event
async def on_member_update(before, after):
    if before.nick != after.nick: 
        print("is it changed?")
        #channel = bot.get_channel(1127200981512372264)
        #await channel.send(msg)

#When member join the server
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1127200981512372264)
    query=f"INSERT INTO {RECORD} (username) VALUES (%s)"
    cur.execute(query,(member.name))
    conn.commit()
    await channel.send(f"Welcome {member.name} to the GAP sever!!!!")

#When member leave the server
@bot.event
async def on_member_remove(member):
    query=f"DELETE FROM {RECORD} WHERE username = (%s)"
    cur.execute(query,(member.name))
    conn.commit()

# When user update their username, the sql username also neeeds to be changed.
@bot.event
async def on_user_update(before,after):
    channel = bot.get_channel(1127200981512372264)
    if before.name!=after.name:
        await channel.send(f'{before.name} has changed name to {after.name}.')
        query = f"UPDATE {RECORD} SET username = %s WHERE username = %s"
        cur.execute(query, (after.name, before.name))
        try:
            cur.execute(query)
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("An error occurred", e)
        
#Update member status and activity
@bot.event
async def on_presence_update(before,after):
    channel = bot.get_channel(1127200981512372264)
    if before.status != after.status:
        await channel.send(f'{before.name} has changed status from {before.status} to {after.status}.')
    #Different activity type print different format
    if before.activity != after.activity and after.activity is not None:
        if after.activity.type == discord.ActivityType.playing:
            await channel.send(f'{before.name} is playing: {after.activity.name}')
        else:
            await channel.send(f'{before.name} says: {after.activity}')

  
@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")

@bot.command()
async def song_help(ctx):
    embed=discord.Embed(title='Songs options')
    embed.add_field(name='To play a song: Type in !play_song #',value='',inline=False)
    embed.add_field(name='Number and corresponding song name below',value='',inline=False)
    embed.add_field(name='',value='1: Whatever It Takes',inline=False)
    await ctx.send(embed=embed)
    
@bot.command()
async def play_song(ctx,num):
    if num == '1':
        print("yes")
        if not ctx.voice_client.is_connected():
            await ctx.author.voice.channel.connect()

        player = await YTDLSource.from_url('https://www.youtube.com/watch?v=M66U_DuMCS8', loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
    await ctx.send(f'Now playing: {player.title}')

@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
    else:
        await ctx.send("The bot is not playing anything at the moment.")

# Use openai's model to create a gpt chatbox.      
def generate_response(message):
    openai_api_url = "https://api.openai.com/v1/engines/text-davinci-002/completions"
    headers = {
        #json type.
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    data = {
        # Prompt means the asking message.
        "prompt": message,
        # Maximum length of output.
        "max_tokens": 60,
    }

    response = requests.post(openai_api_url, headers=headers, json=data)
    #print(response.status_code)
    #print(response.json())
    #Return the answer.
    #return response.json()["choices"][0]["text"]
    try:
        return response.json()["choices"][0]["text"]
    except KeyError:
        print("Received invalid response: ", response.json())
        raise

@bot.command()
async def gptModel(ctx, *,question):
    #Return the answer.
    await ctx.send(f"{generate_response(question)}")

#View every member's level in this server
@bot.command()
async def view(ctx):
    cur.execute(f"SELECT username,level,exp from {RECORD}")
    data=cur.fetchall()
    embed = discord.Embed(title="Level")
    for row in data:
        value="Level: "+str(row[1])+"   Exp: "+str(row[2])
        embed.add_field(name=row[0],value=value,inline=True)
    await ctx.send(embed=embed)

# Command to add motivation sentence to sql table
@bot.command()
async def addSentence(ctx, *,text):
    query = f"INSERT INTO {TABLE} (sentence) VALUES (%s)"
    cur.execute(query, (text,))
    # We have to commit changes in postgresql to save
    conn.commit()

# Print status of member in discord server
@bot.command()
async def status(ctx, member: discord.Member = None):
    # if no member given then print the user's status
    if member is None:
        member = ctx.message.author
    await ctx.send(f'{member.name} is currently {member.status}')

#Homework solver(not working now)
@bot.command()
async def ask(ctx, *, question):
    try:
        # Use wolfram to ask and get answer.
        res = wolfram_client.query(question)
        answer = next(res.results).text
        await ctx.send(answer)
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

# A poll command
@bot.command(name='poll')
async def poll(ctx, question, *options: str):
    if len(options) <= 1:
        await ctx.send('You need more than one option to start a poll!')
        return
    if len(options) > 10:
        await ctx.send('You cannot make a poll for more than 10 things!')
        return

    # Different choices.
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

    # Loop through number of options
    description = []
    for x, option in enumerate(options):
        #Each line an option
        description += '\n {} {}'.format(reactions[x], option)
    
    # The poll page
    embed = discord.Embed(title=question, description=''.join(description))
    react_message = await ctx.send(embed=embed)
    
    #Update the polling result
    for reaction in reactions[:len(options)]:
        await react_message.add_reaction(reaction)
    embed.set_footer(text='Poll ID: {}'.format(react_message.id))
    #Include the poll id
    await react_message.edit(embed=embed)

# Small translator, based on google translate
@bot.command()
async def translate(ctx, *, text):
    # Create a Translator object
    translator = Translator()
    
    # Use the translator object to translate the text to English
    translated = translator.translate(text, dest='en')
    
    # Send the translated text
    await ctx.send(translated.text)

@bot.command()
async def coffee(ctx):
    await ctx.send(file=discord.File("images/coffee.jpg"))
# Small weather report
@bot.command()
async def weather(ctx, *, city: str):
    # http request
    async with aiohttp.ClientSession() as session:
        weather_request = await session.get(
            f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}?unitGroup=metric&key=PA2X242P8HX8B646JGHMNKWUW&contentType=json'
        )
        
        # If input is an invalid city.
        try:
            weather_data = await weather_request.json()
        except json.JSONDecodeError as err:        
            print(f"An error occurred while decoding the JSON: {err}")   
            await ctx.send(f'Sorry, I could not find weather information for the city "{city}". Please make sure the city name is spelled correctly.')     
            return None
        
        # HTTP request ends.
        await session.close()
    
    # Fetch information about wheather 
    address = weather_data['address']
    resolved_address = weather_data['resolvedAddress']
    resolved_address=resolved_address.split(',')[0].strip()
    
    # If input is an invalid city.
    if address.lower() == resolved_address.lower():
        first_day = weather_data['days'][0]
        temp = weather_data['currentConditions']['temp']
        description = first_day['description']
        await ctx.send(f'The weather in {city} is currently {description} with a temperature of {temp}°C')
    else:
        await ctx.send(f'Sorry, I could not find weather information for the city "{city}". Please make sure the city name is spelled correctly.')
       
# Detect the message received.
@bot.event
async def on_message(message):
	# Bot and user have to be different.
    if message.author == bot.user:
        # Get exp when send a message for bot
        query=f"UPDATE {RECORD} SET exp=exp+5 WHERE username = %s"
        try:
            print(query)
            cur.execute(query, (bot.user.name,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("An error occurred", e)
        # For bots, check if they are eligible for level up.
        query=f"SELECT level,exp from {RECORD} WHERE username = %s"
        cur.execute(query, (bot.user.name,))
        val=cur.fetchone()
        if val is not None:
            exceed=int(val[0])*500
            current=int(val[1])
        else:
            print("No such user")
            return
        if current>=exceed:
            over=current-exceed
            await message.channel.send(f"Level UPP for {bot.user.name} to level {int(val[0])+1} !!!!!")
            query=f"UPDATE {RECORD} SET level={int(val[0])+1},exp={over} WHERE username = %s"
            try:
                cur.execute(query, (bot.user.name,))
                conn.commit()
            except Exception as e:
                conn.rollback()
                print("An error occurred", e)
        return
    username = str(message.author).split("#")[0]
    channel = str(message.channel.name)
    user_message = message.content
    print(len(user_message))
    
    # Print the information about message.
    print(f'Message {user_message} by {username} on {channel}')
    
    # Add exp to each user who sends message in this server
    if len(user_message)>0:
        query=f"UPDATE {RECORD} SET exp=exp+5 WHERE username = %s"
        try:
            print(query)
            cur.execute(query, (username,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("An error occurred", e)
    if message.attachments:
        value = len(message.attachments)*10
        query=f"UPDATE {RECORD} SET exp=exp+{value} WHERE username = %s"
        try:
            print(query)
            cur.execute(query, (username,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("An error occurred", e)
    query=f"SELECT level,exp from {RECORD} WHERE username = %s"
    cur.execute(query, (username,))
    val=cur.fetchone()
    if val is not None:
        exceed=int(val[0])*500
        current=int(val[1])
    else:
        print("No such user")
        return
    if current>=exceed:
        over=current-exceed
        await message.channel.send(f"Level UPP for {username} to level {int(val[0])+1} !!!!!")
        query=f"UPDATE {RECORD} SET level={int(val[0])+1},exp={over} WHERE username = %s"
        try:
            cur.execute(query, (username,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("An error occurred", e)
    # Auto translate other non-english text to english
    if len(user_message)>0:
        translator_mes=Translator()
        language=translator_mes.detect(user_message).lang
    # In case not annoying other channel.
    if channel == "bot-test":
        #Convert the integer to binary
        if user_message.isdigit():
            binary=format(int(user_message),'010b')
            await message.channel.send(f'The binary representation of {user_message} is {binary}')
        
        #Send the translated text
        if len(user_message)>0 and language != "en":
            await message.channel.send((translator_mes.translate(user_message,dest='en')).text)
        # Some small text responds.
        if user_message.lower() == "hello" or user_message.lower() == "hi":
            await message.channel.send(f'Now, say my name.')
            return
        elif user_message.lower() == "bye":
            await message.channel.send(f'Bye {username}')
        elif user_message.lower() == "tell me a joke":
            jokes = [" Can someone please shed more\
            light on how my lamp got stolen?",
                     "Why is she called llene? She\
                     stands on equal legs.",
                     "What do you call a gazelle in a \
                     lions territory? Denzel."]
            await message.channel.send(random.choice(jokes))
        #test the daily quote
        elif user_message.lower() == "test":
            await day_quote()
    
    # In order for the all the bots.command to work.
    await bot.process_commands(message)
            
# Start the bot with the token
bot.run(DISCORD_TOKEN)
