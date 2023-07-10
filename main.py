# Importings
import discord
import os
import random
import aiohttp
import json

# Importings and loadings
from dotenv import load_dotenv
from discord.ext import commands
from googletrans import Translator

# Loads the .env file
load_dotenv()

# Grab the dcbot api tokens
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Get all the permissions to dcbot
intents=discord.Intents.default()
intents.message_content=True
intents.presences = True
intents.members = True

#Create an instance of bot
bot = commands.Bot(command_prefix='!',intents=intents)

# dcbot gets activated
@bot.event
async def on_ready():
	# Number of how many servers dcbot has connected to
	guild_count = 0

	# Loop through all bots's guilds/server
	for guild in bot.guilds:
		print(f"- {guild.id} (name: {guild.name})")

		guild_count = guild_count + 1

	print("GAP is in " + str(guild_count) + " guilds.")

# Should print the updated member status, but not working
@bot.event
async def on_member_update(before, after):
    if before.status != after.status:
        print("Not working")
        #channel = bot.get_channel(1127200981512372264) # Replace 'ID' with your channel ID
        #await channel.send(f'{before.name} has changed status from {before.status} to {after.status}.')

# Print status of member in discord server
@bot.command()
async def status(ctx, member: discord.Member = None):
    # if no member given then print the user's status
    if member is None:
        member = ctx.message.author
    await ctx.send(f'{member.name} is currently {member.status}')

# Small translator, based on google translate
@bot.command()
async def translate(ctx, *, text):
    # Create a Translator object
    translator = Translator()
    
    # Use the translator object to translate the text to English
    translated = translator.translate(text, dest='en')
    
    # Send the translated text
    await ctx.send(translated.text)

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
        return
    username = str(message.author).split("#")[0]
    channel = str(message.channel.name)
    user_message = message.content
    
    # Print the information about message.
    print(f'Message {user_message} by {username} on {channel}')
    
    # In case not annoying other channel.
    if channel == "bot-test":
        
        #Convert the integer to binary
        if user_message.isdigit():
            binary=format(int(user_message),'010b')
            await message.channel.send(f'The binary representation of {user_message} is {binary}')
            
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
    
    # In order for the all the bots.command to work.
    await bot.process_commands(message)
            
# Start the bot with the token
bot.run(DISCORD_TOKEN)
