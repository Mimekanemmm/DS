import discord
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Hugging Face Inference API details
API_URL = "https://api-inference.huggingface.co/models/deepseek-ai/DeepSeek-R1"
headers = {"Authorization": f"Bearer {os.getenv('HUGGING_FACE_TOKEN')}"}

# Function to query the Hugging Face API
def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

# Event: When the bot is ready
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

# Event: When a message is sent in the server
@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Prepare the payload for the Hugging Face API
    payload = {"inputs": message.content}

    try:
        # Get the response from the Hugging Face API
        response = query(payload)
        generated_text = response[0]['generated_text']  # Extract the generated text
        await message.channel.send(generated_text)  # Send the response back to Discord
    except Exception as e:
        print(f"Error: {e}")
        await message.channel.send("Sorry, I couldn't generate a response. Please try again later.")

# Run the bot using the token from environment variables
client.run(os.getenv('DISCORD_BOT_TOKEN'))