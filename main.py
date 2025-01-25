import discord
from discord.ext import commands
import requests
import os
import time
import asyncio
from dotenv import load_dotenv
from flask import Flask
import threading

# Load environment variables from .env file
load_dotenv()

# Get environment variables
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
HUGGING_FACE_TOKEN = os.getenv('HUGGING_FACE_TOKEN')

# Validate environment variables
if DISCORD_BOT_TOKEN is None:
    raise ValueError("Discord bot token not found in environment variables. Please set DISCORD_BOT_TOKEN.")
if HUGGING_FACE_TOKEN is None:
    raise ValueError("Hugging Face token not found in environment variables. Please set HUGGING_FACE_TOKEN.")

print("Tokens loaded successfully!")

# Set up Flask app for Render's port requirement
app = Flask(__name__)

@app.route('/')
def home():
    return "Discord bot is running!"

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Hugging Face Inference API details
API_URL = "https://api-inference.huggingface.co/models/deepseek-ai/DeepSeek-R1"
headers = {"Authorization": f"Bearer {HUGGING_FACE_TOKEN}"}

# Function to query the Hugging Face API with retry logic
def query(payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            if response.status_code == 429:  # Rate limit
                retry_after = int(response.headers.get('retry-after', 60))
                time.sleep(retry_after)
                continue
            return response.json()
        except requests.exceptions.Timeout:
            if attempt == max_retries - 1:
                raise
            time.sleep(5)
    return {"error": "Max retries exceeded"}

# Event: When the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Command: !ask
@bot.command(name='ask')
async def ask(ctx, *, question):
    payload = {
        "inputs": question,
        "parameters": {
            "max_length": 100,
            "temperature": 0.7,
            "top_p": 0.95,
            "do_sample": True
        }
    }

    try:
        async with ctx.typing():
            response = await asyncio.to_thread(query, payload)
            
            # Check if response is an error message
            if isinstance(response, dict) and "error" in response:
                raise Exception(response["error"])
                
            # Handle the response correctly
            if isinstance(response, list) and len(response) > 0:
                if isinstance(response[0], dict) and "generated_text" in response[0]:
                    generated_text = response[0]["generated_text"]
                else:
                    generated_text = response[0]
            else:
                generated_text = str(response)

            # Ensure the response isn't too long for Discord
            if len(generated_text) > 2000:
                generated_text = generated_text[:1997] + "..."

            await ctx.send(generated_text)
    except Exception as e:
        error_message = f"Error: {str(e)}"
        print(error_message)
        await ctx.send(error_message)

# Function to run the Flask app
def run_flask():
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# Function to run the Discord bot
def run_bot():
    bot.run(DISCORD_BOT_TOKEN)

# Run Flask and Discord bot in separate threads
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    bot_thread = threading.Thread(target=run_bot)

    flask_thread.start()
    bot_thread.start()
