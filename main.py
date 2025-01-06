import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import asyncio
import requests
from dotenv import load_dotenv
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from stability_sdk import client
import io
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
STABILITY_KEY = os.getenv('STABILITY_KEY')

# Initialize Stability AI client
stability_api = client.StabilityInference(
    key=STABILITY_KEY,
    verbose=True,
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    welcome_message = (
        "🎨 Welcome to DreamWeaver AI! 🌟\n\n"
        "I'm your creative companion, ready to transform your imagination into stunning images. "
        "Here's what I can do:\n\n"
        "🎯 Generate unique images from your text descriptions\n"
        "🖼 Create artistic interpretations of your ideas\n"
        "✨ Transform your concepts into visual reality\n\n"
        "To get started, simply:\n"
        "1. Use /generate command\n"
        "2. Type your detailed image description\n"
        "3. Wait for the magic to happen!\n\n"
        "Example: /generate a magical forest with glowing butterflies at sunset"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = (
        "🤖 DreamWeaver AI Help Guide 🌟\n\n"
        "Commands:\n"
        "/start - Start the bot and see welcome message\n"
        "/generate - Create an image from your text description\n"
        "/help - Show this help message\n\n"
        "Tips for better results:\n"
        "• Be specific in your descriptions\n"
        "• Include details about style, mood, and lighting\n"
        "• Mention colors and composition preferences"
    )
    await update.message.reply_text(help_text)

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /generate command."""
    await update.message.reply_text(
        "🎨 Please enter your image description after /generate.\n"
        "Example: /generate sunset over mountain peaks with northern lights"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages and generate images."""
    message_text = update.message.text
    
    # Check if message starts with /generate
    if message_text.startswith('/generate '):
        prompt = message_text[9:].strip()  # Remove '/generate ' from the start
        if not prompt:
            await update.message.reply_text("Please provide a description after /generate")
            return
            
        # Send "generating" message
        status_message = await update.message.reply_text("🎨 Generating your image... Please wait!")
        
        try:
            # Generate image using Stability AI
            answers = stability_api.generate(
                prompt=prompt,
                seed=int(time.time()),  # Random seed
                steps=30,
                cfg_scale=7.0,
                width=512,
                height=512,
                samples=1,
                sampler=generation.SAMPLER_K_DPMPP_2M
            )

            # Process and send the generated image
            for resp in answers:
                for artifact in resp.artifacts:
                    if artifact.type == generation.ARTIFACT_IMAGE:
                        img = io.BytesIO(artifact.binary)
                        img.seek(0)
                        
                        # Send the image with the original prompt
                        await update.message.reply_photo(
                            photo=img,
                            caption=f"🎨 Generated image for: '{prompt}'"
                        )
                        await status_message.delete()
                        return

        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            await status_message.edit_text("❌ Sorry, there was an error generating your image. Please try again later.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        await update.message.reply_text("Sorry, something went wrong. Please try again later.")
    except:
        pass

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("generate", generate_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Add error handler
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
