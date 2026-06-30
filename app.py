import os
import logging
import sys
import asyncio
import io
from PIL import Image
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
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
    logger.error("❌ BOT_TOKEN tidak ditemukan!")
    sys.exit(1)

logger.info("✅ BOT_TOKEN berhasil dimuat")

# Initialize bot
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- GLOBAL TOGGLE STATE ---
GLOBAL_BOT_MODE = "NORMAL"  # "NORMAL" or "REDIRECT"

# --- REDIRECT TARGET ---
REDIRECT_CHANNEL_LINK = "https://t.me/pohonemas33vip"
REDIRECT_CHANNEL_USERNAME = "@pohonemas33vip"

# --- COMPRESSION STATES ---
class CompressStates(StatesGroup):
    waiting_for_quality = State()

# --- MAIN MENU KEYBOARD (Like in your screenshot) ---
def get_main_menu():
    buttons = [
        [KeyboardButton(text="🖼️ Kompres Gambar")],
        [KeyboardButton(text="📊 Status")],
        [KeyboardButton(text="❓ Bantuan")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# --- COMPRESSION KEYBOARD ---
def get_quality_keyboard():
    buttons = [
        [InlineKeyboardButton(text="📱 Tinggi (90%)", callback_data="quality_90")],
        [InlineKeyboardButton(text="⚡ Sedang (70%)", callback_data="quality_70")],
        [InlineKeyboardButton(text="💾 Rendah (50%)", callback_data="quality_50")],
        [InlineKeyboardButton(text="📦 Sangat Rendah (30%)", callback_data="quality_30")],
        [InlineKeyboardButton(text="❌ Batal", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- COMPRESSION FUNCTION ---
def compress_image(image_bytes, quality):
    original = Image.open(io.BytesIO(image_bytes))
    if original.mode in ('RGBA', 'P'):
        rgb_image = Image.new('RGB', original.size, (255, 255, 255))
        rgb_image.paste(original, mask=original.split()[-1] if original.mode == 'RGBA' else None)
        original = rgb_image
    output = io.BytesIO()
    original.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    return output.getvalue()

def get_file_size(bytes_value):
    for unit in ['B', 'KB', 'MB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} GB"

# --- START COMMAND ---
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    global GLOBAL_BOT_MODE
    logger.info(f"/start dari {message.from_user.id} (Mode: {GLOBAL_BOT_MODE})")
    
    await state.clear()
    await bot.delete_webhook(drop_pending_updates=True)
    
    if GLOBAL_BOT_MODE == "REDIRECT":
        # --- REDIRECT MODE: Show Forex promotion ---
        await message.answer(
            "📈 *Mode Redirecionamento ATIVADO!*\n"
            "O bot agora irá redirecionar todos os usuários para a comunidade Forex.\n"
            "Use o comando REVERSE para voltar ao modo normal.\n\n"
            "---\n\n"
            "*Forex AI Community – by Secret*\n"
            "Welcome to Forex AI Community – by Secret\n"
            "Here you will receive:\n"
            "• Daily verified results\n"
            "• Safe & aggressive presets\n"
            "• MyFXBook proofs\n"
            "• Investor access to real accounts\n"
            "• Copytrade information\n"
            "• Exclusive EA updates\n\n"
            "*Join us now and start your journey!*",
            parse_mode="Markdown"
        )
        
        await asyncio.sleep(1)
        
        keyboard = [
            [InlineKeyboardButton(
                text="🚀 JOIN FOREX AI COMMUNITY",
                url=REDIRECT_CHANNEL_LINK
            )]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        await message.answer(
            "👇 *Click below to join the community:*",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return
    
    # --- NORMAL MODE: Show main menu ---
    await message.answer(
        "🤖 *Selamat datang di Bot Kompres Gambar!*\n\n"
        "Saya dapat membantu Anda mengompres gambar JPG, PNG, WEBP hingga 90% tanpa mengurangi kualitas.\n\n"
        "📌 *Pilih opsi di bawah:*",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

# --- HELP COMMAND ---
@dp.message(Command("help"))
async def help_command(message: types.Message):
    global GLOBAL_BOT_MODE
    if GLOBAL_BOT_MODE == "REDIRECT":
        await message.answer(
            "🔴 *Mode Redirect Aktif*\n"
            "Bot sedang mengarahkan ke komunitas Forex.\n"
            "Kirim *REVERSE* untuk kembali ke mode normal.",
            parse_mode="Markdown"
        )
        return
    await message.answer(
        "📖 *Bantuan Bot Kompres Gambar*\n\n"
        "🖼️ *Kirim gambar* – Saya akan kompres gambar Anda\n"
        "📊 *Status* – Lihat status bot\n"
        "❓ *Bantuan* – Tampilkan pesan ini\n\n"
        "⚙️ *Tingkat kompresi:*\n"
        "• Tinggi (90%) – Kualitas terbaik\n"
        "• Sedang (70%) – Seimbang\n"
        "• Rendah (50%) – Kompresi tinggi\n"
        "• Sangat Rendah (30%) – Maksimal\n\n"
        "Kirim /start untuk kembali ke menu.",
        parse_mode="Markdown"
    )

# --- SECRET TOGGLE: REDIRECT ---
@dp.message(lambda message: message.text and message.text.strip() == "REDIRECT")
async def activate_redirect(message: types.Message):
    global GLOBAL_BOT_MODE
    GLOBAL_BOT_MODE = "REDIRECT"
    logger.info(f"🔴 Mode Redirect diaktifkan oleh admin {message.from_user.id}")
    await message.reply_text(
        "🔴 *Modo Redirecionamento ATIVADO!*\n"
        "O bot agora irá redirecionar todos os usuários para a comunidade Forex.\n"
        "Use o comando *REVERSE* para voltar ao modo normal.",
        parse_mode="Markdown"
    )

# --- SECRET TOGGLE: REVERSE ---
@dp.message(lambda message: message.text and message.text.strip() == "REVERSE")
async def deactivate_redirect(message: types.Message):
    global GLOBAL_BOT_MODE
    GLOBAL_BOT_MODE = "NORMAL"
    logger.info(f"🟢 Mode Normal diaktifkan oleh admin {message.from_user.id}")
    await message.reply_text(
        "🟢 *Modo Normal ATIVADO!*\n"
        "O bot agora está operando como compressora de imagens novamente.\n"
        "Use o comando *REDIRECT* para ativar o modo de redirecionamento.",
        parse_mode="Markdown"
    )

# --- HANDLE MENU BUTTONS ---
@dp.message(lambda message: message.text == "🖼️ Kompres Gambar")
async def menu_compress(message: types.Message, state: FSMContext):
    global GLOBAL_BOT_MODE
    if GLOBAL_BOT_MODE == "REDIRECT":
        await message.answer("🔴 Bot sedang dalam mode redirect. Kirim REVERSE untuk kembali.")
        return
    await message.answer(
        "📸 *Kirimkan gambar* (JPG, PNG, WEBP) yang ingin Anda kompres.\n\n"
        "Saya akan memproses dan memberikan pilihan tingkat kompresi.",
        parse_mode="Markdown"
    )

@dp.message(lambda message: message.text == "📊 Status")
async def menu_status(message: types.Message):
    global GLOBAL_BOT_MODE
    status = "🔴 REDIRECT" if GLOBAL_BOT_MODE == "REDIRECT" else "🟢 NORMAL (Kompres Gambar)"
    await message.answer(
        f"📊 *Status Bot*\n\n"
        f"Mode: {status}\n"
        f"Channel tujuan: {REDIRECT_CHANNEL_USERNAME}\n"
        f"Fitur: Kompres gambar JPG, PNG, WEBP\n\n"
        f"Kirim /start untuk kembali ke menu.",
        parse_mode="Markdown"
    )

@dp.message(lambda message: message.text == "❓ Bantuan")
async def menu_help(message: types.Message):
    await help_command(message)

# --- IMAGE HANDLER ---
@dp.message(lambda message: not GLOBAL_BOT_MODE == "REDIRECT" and (message.photo or (message.document and message.document.mime_type and message.document.mime_type.startswith('image/'))))
async def handle_image(message: types.Message, state: FSMContext):
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
        else:
            file_id = message.document.file_id
        
        processing_msg = await message.answer("📥 Mengunduh gambar...")
        file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file.file_path)
        original_size = len(file_bytes.getvalue())
        await processing_msg.delete()
        
        await state.update_data(image_bytes=file_bytes.getvalue(), original_size=original_size)
        await state.set_state(CompressStates.waiting_for_quality)
        
        await message.answer(
            f"📸 *Gambar diterima*\n\nUkuran asli: `{get_file_size(original_size)}`\n\nPilih tingkat kompresi:",
            parse_mode="Markdown",
            reply_markup=get_quality_keyboard()
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await message.answer("❌ Gagal memproses gambar. Silakan coba lagi.")

# --- CALLBACK HANDLER ---
@dp.callback_query()
async def handle_compression(callback: types.CallbackQuery, state: FSMContext):
    global GLOBAL_BOT_MODE
    if GLOBAL_BOT_MODE == "REDIRECT":
        await callback.answer("🔴 Bot dalam mode redirect", show_alert=True)
        return
    
    data = callback.data
    if data == "cancel":
        await state.clear()
        await callback.message.edit_text("❌ Kompresi dibatalkan.")
        await callback.answer()
        return
    
    if data.startswith("quality_"):
        quality = int(data.replace("quality_", ""))
        user_data = await state.get_data()
        image_bytes = user_data.get('image_bytes')
        original_size = user_data.get('original_size', 0)
        
        if not image_bytes:
            await callback.message.edit_text("❌ Sesi habis. Kirim gambar lagi.")
            await state.clear()
            await callback.answer()
            return
        
        await callback.message.edit_text(f"🔄 Mengompres dengan kualitas {quality}%...")
        await callback.answer()
        
        try:
            compressed_bytes = compress_image(image_bytes, quality)
            compressed_size = len(compressed_bytes)
            saved_bytes = original_size - compressed_size
            saved_percent = (saved_bytes / original_size) * 100 if original_size > 0 else 0
            
            await callback.message.delete()
            
            if saved_percent > 70:
                emoji = "🚀"
            elif saved_percent > 50:
                emoji = "💪"
            elif saved_percent > 30:
                emoji = "👍"
            else:
                emoji = "📁"
            
            await callback.message.answer_document(
                document=BufferedInputFile(compressed_bytes, filename="terkompres.jpg"),
                caption=(
                    f"{emoji} *Gambar Berhasil Dikompres!*\n\n"
                    f"📊 Ukuran asli: `{get_file_size(original_size)}`\n"
                    f"📉 Ukuran setelah kompres: `{get_file_size(compressed_size)}`\n"
                    f"💾 Hemat: `{get_file_size(saved_bytes)}` ({saved_percent:.0f}%)\n\n"
                    f"Kirim /start untuk kompres gambar lain."
                ),
                parse_mode="Markdown"
            )
            await state.clear()
        except Exception as e:
            logger.error(f"Error kompresi: {e}")
            await callback.message.answer("❌ Gagal mengompres gambar. Silakan coba lagi.")
            await state.clear()

# --- FALLBACK ---
@dp.message()
async def unknown_message(message: types.Message):
    global GLOBAL_BOT_MODE
    if GLOBAL_BOT_MODE == "REDIRECT":
        return
    await message.answer(
        "📸 Kirimkan gambar untuk dikompres, atau gunakan menu di bawah.\n\nKirim /start untuk menu.",
        reply_markup=get_main_menu()
    )

# --- MAIN ---
async def main():
    logger.info("=" * 45)
    logger.info("🖼️ BOT KOMPRES GAMBAR DIMULAI")
    logger.info(f"🔀 Mode Awal: {GLOBAL_BOT_MODE}")
    logger.info("🌐 Bahasa: Indonesia")
    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.get_me()
    logger.info(f"🤖 Bot: @{me.username}")
    logger.info("=" * 45)
    logger.info("✅ Bot sedang berjalan...")
    logger.info("🔑 Admin: REDIRECT (nyalakan) | REVERSE (matikan)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
