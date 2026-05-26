import os
import logging
import sys
import asyncio
import io
from PIL import Image
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Check for BOT_TOKEN
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not set!")
    sys.exit(1)

logger.info("✅ BOT_TOKEN loaded")

# Initialize bot
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Compression states
class CompressStates(StatesGroup):
    waiting_for_quality = State()

def get_quality_keyboard():
    buttons = [
        [InlineKeyboardButton(text="📱 High (90%)", callback_data="quality_90")],
        [InlineKeyboardButton(text="⚡ Medium (70%)", callback_data="quality_70")],
        [InlineKeyboardButton(text="💾 Low (50%)", callback_data="quality_50")],
        [InlineKeyboardButton(text="📦 Very Low (30%)", callback_data="quality_30")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def compress_image(image_bytes, quality):
    """Compress image to target quality"""
    original = Image.open(io.BytesIO(image_bytes))
    
    # Convert RGBA to RGB for JPEG
    if original.mode in ('RGBA', 'P'):
        rgb_image = Image.new('RGB', original.size, (255, 255, 255))
        rgb_image.paste(original, mask=original.split()[-1] if original.mode == 'RGBA' else None)
        original = rgb_image
    
    # Save compressed image
    output = io.BytesIO()
    original.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    
    return output.getvalue()

def get_file_size(bytes_value):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} GB"

@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    logger.info(f"/start from {message.from_user.id}")
    
    # Clear state and webhook
    await state.clear()
    await bot.delete_webhook(drop_pending_updates=True)
    
    await message.answer(
        "🖼️ *Image Compressor Bot*\n\n"
        "Reduce image file size while keeping good quality.\n\n"
        "📌 *How to use:*\n"
        "1. Send me an image (JPG, PNG, WEBP)\n"
        "2. Choose compression level\n"
        "3. Get your compressed image!\n\n"
        "✨ *Features:*\n"
        "- Reduces file size up to 90%\n"
        "- Preserves image quality\n"
        "- Fast processing\n"
        "- No watermarks\n\n"
        "Send me an image to start!",
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "📖 *Commands:*\n"
        "/start - Compress an image\n"
        "/help - Show this help\n"
        "/cancel - Cancel operation\n\n"
        "⚙️ *Compression levels:*\n"
        "• High (90%) - Minimal size reduction\n"
        "• Medium (70%) - Good balance\n"
        "• Low (50%) - Significant reduction\n"
        "• Very Low (30%) - Maximum compression\n\n"
        "Send /start to begin!",
        parse_mode="Markdown"
    )

@dp.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Operation cancelled. Send /start to try again.")

@dp.message(lambda message: message.photo or (message.document and message.document.mime_type and message.document.mime_type.startswith('image/')))
async def handle_image(message: types.Message, state: FSMContext):
    try:
        # Get image file
        if message.photo:
            file_id = message.photo[-1].file_id
            file_name = "image.jpg"
        else:
            file_id = message.document.file_id
            file_name = message.document.file_name or "image.jpg"
        
        # Download image
        processing_msg = await message.answer("📥 Downloading image...")
        
        file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file.file_path)
        original_size = len(file_bytes.getvalue())
        
        await processing_msg.delete()
        
        # Store image data
        await state.update_data(image_bytes=file_bytes.getvalue(), file_name=file_name, original_size=original_size)
        await state.set_state(CompressStates.waiting_for_quality)
        
        await message.answer(
            f"📸 *Image received*\n\n"
            f"Original size: `{get_file_size(original_size)}`\n\n"
            f"Choose compression level:",
            parse_mode="Markdown",
            reply_markup=get_quality_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await message.answer("❌ Failed to process image. Please try again.")

@dp.callback_query()
async def handle_compression(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data
    
    if data == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Compression cancelled. Send /start to try again.")
        await callback.answer()
        return
    
    if data.startswith("quality_"):
        quality = int(data.replace("quality_", ""))
        
        user_data = await state.get_data()
        image_bytes = user_data.get('image_bytes')
        original_size = user_data.get('original_size', 0)
        
        if not image_bytes:
            await callback.message.edit_text("❌ Session expired. Send image again.")
            await state.clear()
            await callback.answer()
            return
        
        await callback.message.edit_text(f"🔄 Compressing image at {quality}% quality...")
        await callback.answer()
        
        try:
            # Compress image
            compressed_bytes = compress_image(image_bytes, quality)
            compressed_size = len(compressed_bytes)
            
            # Calculate savings
            saved_bytes = original_size - compressed_size
            saved_percent = (saved_bytes / original_size) * 100 if original_size > 0 else 0
            
            # Send result
            await callback.message.delete()
            
            # Determine which emoji to show
            if saved_percent > 70:
                emoji = "🚀"
            elif saved_percent > 50:
                emoji = "💪"
            elif saved_percent > 30:
                emoji = "👍"
            else:
                emoji = "📁"
            
            await callback.message.answer_document(
                document=BufferedInputFile(compressed_bytes, filename="compressed.jpg"),
                caption=f"{emoji} *Image Compressed!*\n\n"
                       f"📊 Original: `{get_file_size(original_size)}`\n"
                       f"📉 Compressed: `{get_file_size(compressed_size)}`\n"
                       f"💾 Saved: `{get_file_size(saved_bytes)}` ({saved_percent:.0f}%)\n\n"
                       f"Send /start to compress another image.",
                parse_mode="Markdown"
            )
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Compression error: {e}")
            await callback.message.answer("❌ Failed to compress image. Please try again.")
            await state.clear()

@dp.message()
async def unknown_message(message: types.Message):
    await message.answer(
        "📸 Please send an image to compress.\n\n"
        "Send /start for instructions.",
        parse_mode="Markdown"
    )

async def main():
    logger.info("=" * 45)
    logger.info("🖼️ IMAGE COMPRESSOR BOT STARTING")
    
    # Delete webhook on startup
    await bot.delete_webhook(drop_pending_updates=True)
    
    me = await bot.get_me()
    logger.info(f"🤖 Bot: @{me.username}")
    logger.info(f"🆔 Bot ID: {me.id}")
    logger.info("=" * 45)
    logger.info("✅ Bot is polling for messages...")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
