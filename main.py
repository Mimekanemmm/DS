import discord
import requests
import os
from dotenv import load_dotenv
from flask import Flask
import threading

# Load environment variables from .env file (for local development)
load_dotenv()

# Debugging: Print the tokens to verify they're being loaded correctly
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
HUGGING_FACE_TOKEN = os.getenv('HUGGING_FACE_TOKEN')

if DISCORD_BOT_TOKEN is None:
    raise ValueError("Discord bot token not found in environment variables. Please set DISCORD_BOT_TOKEN.")
if HUGGING_FACE_TOKEN is None:
    raise ValueError("Hugging Face token not found in environment variables. Please set HUGGING_FACE_TOKEN.")

print("Tokens loaded successfully!")  # Debugging: Confirm tokens are loaded

# Set up Flask app for Render's port requirement
app = Flask(__name__)

@app.route('/')
def home():
    return "Discord bot is running!"

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Hugging Face Inference API details
API_URL = "https://api-inference.huggingface.co/models/deepseek-ai/DeepSeek-R1"
headers = {"Authorization": f"Bearer {HUGGING_FACE_TOKEN}"}

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

# Function to run the Flask app
def run_flask():
    port = int(os.getenv('PORT', 5000))  # Use PORT if set, otherwise default to 5000
    app.run(host='0.0.0.0', port=port)

# Function to run the Discord bot
def run_bot():
    client.run(DISCORD_BOT_TOKEN)

# Run Flask and Discord bot in separate threads
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    bot_thread = threading.Thread(target=run_bot)

    flask_thread.start()
    bot_thread.start()