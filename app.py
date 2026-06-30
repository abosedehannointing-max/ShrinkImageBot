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
    logger.error("❌ BOT_TOKEN tidak ditemukan!")
    sys.exit(1)

logger.info("✅ BOT_TOKEN berhasil dimuat")

# Initialize bot
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- GLOBAL TOGGLE STATE ---
GLOBAL_BOT_MODE = "LOGO"  # "LOGO" (normal/kompres) or "REDIRECT" (funnel)

# --- REDIRECT TARGET ---
REDIRECT_CHANNEL_LINK = "https://t.me/pohonemas33vip"
REDIRECT_CHANNEL_USERNAME = "@pohonemas33vip"

# --- COMPRESSION LOGIC (Normal Mode) ---
class CompressStates(StatesGroup):
    waiting_for_quality = State()

# --- SEMUA TEKS DALAM BAHASA INDONESIA ---
TEXTS = {
    "welcome": (
        "🖼️ *Bot Kompres Gambar*\n\n"
        "Perkecil ukuran file gambar tanpa mengurangi kualitas.\n\n"
        "📌 *Cara menggunakan:*\n"
        "1. Kirimkan gambar (JPG, PNG, WEBP)\n"
        "2. Pilih tingkat kompresi\n"
        "3. Dapatkan gambar yang sudah dikompres!\n\n"
        "✨ *Fitur:*\n"
        "- Mengurangi ukuran file hingga 90%\n"
        "- Menjaga kualitas gambar\n"
        "- Tanpa watermark\n"
        "- 100% gratis\n\n"
        "Kirimkan gambar untuk memulai!"
    ),
    "help": (
        "📖 *Perintah:*\n"
        "/start - Kompres gambar\n"
        "/help - Bantuan ini\n"
        "/cancel - Batalkan\n\n"
        "⚙️ *Tingkat kompresi:*\n"
        "• Tinggi (90%) - Pengurangan minimal\n"
        "• Sedang (70%) - Keseimbangan baik\n"
        "• Rendah (50%) - Pengurangan signifikan\n"
        "• Sangat Rendah (30%) - Kompresi maksimal\n\n"
        "Kirim /start untuk memulai!"
    ),
    "cancel": "❌ Operasi dibatalkan. Kirim /start untuk mencoba lagi.",
    "high_btn": "📱 Tinggi (90%)",
    "medium_btn": "⚡ Sedang (70%)",
    "low_btn": "💾 Rendah (50%)",
    "very_low_btn": "📦 Sangat Rendah (30%)",
    "cancel_btn": "❌ Batal",
    "downloading": "📥 Mengunduh gambar...",
    "image_received": "📸 *Gambar diterima*\n\nUkuran asli: `{size}`\n\nPilih tingkat kompresi:",
    "compressing": "🔄 Mengompres gambar dengan kualitas {quality}%...",
    "compress_success": (
        "{emoji} *Gambar Berhasil Dikompres!*\n\n"
        "📊 Ukuran asli: `{original}`\n"
        "📉 Ukuran setelah kompres: `{compressed}`\n"
        "💾 Hemat: `{saved}` ({percent}%)\n\n"
        "Kirim /start untuk kompres gambar lain."
    ),
    "compress_failed": "❌ Gagal mengompres gambar. Silakan coba lagi.",
    "error": "❌ Terjadi kesalahan. Silakan coba lagi.",
    "no_image": "📸 Kirimkan gambar untuk dikompres.\n\nKirim /start untuk petunjuk.",
    "please_send_image": "📸 Kirimkan gambar untuk dikompres.\n\nGunakan tombol di bawah atau ketik /cancel untuk membatalkan.",
    "session_expired": "❌ Sesi habis. Kirim gambar lagi.",
    "redirect_welcome": (
        "📈 *Di tengah ketidakpastian ekonomi, memiliki penghasilan pasif sangat penting.*\n\n"
        "Kami memberikan EA gratis yang memungkinkan Anda menghasilkan uang dengan mudah secara otomatis.\n\n"
        "Hubungi @sonic_fx_tutor untuk bimbingan."
    ),
    "redirect_button": "🚀 Klik untuk Bergabung Sekarang",
    "redirect_footer": f"👉 Bergabunglah dengan channel VIP kami: {REDIRECT_CHANNEL_USERNAME}"
}

def get_quality_keyboard():
    buttons = [
        [InlineKeyboardButton(text=TEXTS["high_btn"], callback_data="quality_90")],
        [InlineKeyboardButton(text=TEXTS["medium_btn"], callback_data="quality_70")],
        [InlineKeyboardButton(text=TEXTS["low_btn"], callback_data="quality_50")],
        [InlineKeyboardButton(text=TEXTS["very_low_btn"], callback_data="quality_30")],
        [InlineKeyboardButton(text=TEXTS["cancel_btn"], callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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

# --- START COMMAND (With Toggle) ---
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    global GLOBAL_BOT_MODE
    logger.info(f"/start dari {message.from_user.id} (Mode: {GLOBAL_BOT_MODE})")

    # Clear state
    await state.clear()
    await bot.delete_webhook(drop_pending_updates=True)

    # --- REDIRECT MODE ---
    if GLOBAL_BOT_MODE == "REDIRECT":
        # Send promotional text in Indonesian
        await message.answer(
            TEXTS["redirect_welcome"],
            parse_mode="Markdown"
        )

        await asyncio.sleep(1)

        # Create and send the inline keyboard with the join button
        keyboard = [
            [InlineKeyboardButton(
                text=TEXTS["redirect_button"],
                url=REDIRECT_CHANNEL_LINK
            )]
        ]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        await message.answer(
            TEXTS["redirect_footer"],
            reply_markup=reply_markup
        )
        return

    # --- NORMAL MODE (Image Compression in Indonesian) ---
    await message.answer(
        TEXTS["welcome"],
        parse_mode="Markdown"
    )

# --- HELP COMMAND (Disabled in Redirect Mode) ---
@dp.message(Command("help"))
async def help_command(message: types.Message):
    global GLOBAL_BOT_MODE
    if GLOBAL_BOT_MODE == "REDIRECT":
        return
    await message.answer(TEXTS["help"], parse_mode="Markdown")

# --- CANCEL COMMAND (Disabled in Redirect Mode) ---
@dp.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext):
    global GLOBAL_BOT_MODE
    if GLOBAL_BOT_MODE == "REDIRECT":
        return
    await state.clear()
    await message.answer(TEXTS["cancel"])

# --- SECRET TOGGLE: REDIRECT ---
@dp.message(lambda message: message.text and message.text.strip() == "REDIRECT")
async def activate_redirect(message: types.Message):
    global GLOBAL_BOT_MODE
    GLOBAL_BOT_MODE = "REDIRECT"
    logger.info(f"🔴 Mode redirect diaktifkan oleh admin {message.from_user.id}")
    await message.reply_text(
        "✅ *Mode Redirect Diaktifkan!*\n"
        "Bot sekarang akan mengarahkan pengguna ke @pohonemas33vip.\n"
        "Kirim *REVERSE* untuk kembali ke mode normal.",
        parse_mode="Markdown"
    )

# --- SECRET TOGGLE: REVERSE (Back to Normal) ---
@dp.message(lambda message: message.text and message.text.strip() == "REVERSE")
async def deactivate_redirect(message: types.Message):
    global GLOBAL_BOT_MODE
    GLOBAL_BOT_MODE = "LOGO"
    logger.info(f"🟢 Mode normal dikembalikan oleh admin {message.from_user.id}")
    await message.reply_text(
        "✅ *Mode Normal Diaktifkan!*\n"
        "Bot sekarang menjadi alat kompres gambar lagi.\n"
        "Kirim *REDIRECT* untuk mengaktifkan mode redirect.",
        parse_mode="Markdown"
    )

# --- IMAGE HANDLER (Only in Normal Mode) ---
@dp.message(lambda message: not GLOBAL_BOT_MODE == "REDIRECT" and (message.photo or (message.document and message.document.mime_type and message.document.mime_type.startswith('image/'))))
async def handle_image(message: types.Message, state: FSMContext):
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
        else:
            file_id = message.document.file_id

        processing_msg = await message.answer(TEXTS["downloading"])
        file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file.file_path)
        original_size = len(file_bytes.getvalue())
        await processing_msg.delete()

        await state.update_data(image_bytes=file_bytes.getvalue(), original_size=original_size)
        await state.set_state(CompressStates.waiting_for_quality)

        await message.answer(
            TEXTS["image_received"].format(size=get_file_size(original_size)),
            parse_mode="Markdown",
            reply_markup=get_quality_keyboard()
        )
    except Exception as e:
        logger.error(f"Error handling gambar: {e}")
        await message.answer(TEXTS["error"])

# --- CALLBACK QUERY HANDLER (Disabled in Redirect Mode) ---
@dp.callback_query()
async def handle_compression(callback: types.CallbackQuery, state: FSMContext):
    global GLOBAL_BOT_MODE
    if GLOBAL_BOT_MODE == "REDIRECT":
        await callback.answer()
        return

    data = callback.data
    if data == "cancel":
        await state.clear()
        await callback.message.edit_text(TEXTS["cancel"])
        await callback.answer()
        return

    if data.startswith("quality_"):
        quality = int(data.replace("quality_", ""))
        user_data = await state.get_data()
        image_bytes = user_data.get('image_bytes')
        original_size = user_data.get('original_size', 0)

        if not image_bytes:
            await callback.message.edit_text(TEXTS["session_expired"])
            await state.clear()
            await callback.answer()
            return

        await callback.message.edit_text(TEXTS["compressing"].format(quality=quality))
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
                caption=TEXTS["compress_success"].format(
                    emoji=emoji,
                    original=get_file_size(original_size),
                    compressed=get_file_size(compressed_size),
                    saved=get_file_size(saved_bytes),
                    percent=f"{saved_percent:.0f}"
                ),
                parse_mode="Markdown"
            )
            await state.clear()
        except Exception as e:
            logger.error(f"Error kompresi: {e}")
            await callback.message.answer(TEXTS["compress_failed"])
            await state.clear()

# --- FALLBACK MESSAGE HANDLER ---
@dp.message()
async def unknown_message(message: types.Message):
    global GLOBAL_BOT_MODE
    if GLOBAL_BOT_MODE == "REDIRECT":
        return
    await message.answer(TEXTS["no_image"], parse_mode="Markdown")

# --- MAIN ---
async def main():
    logger.info("=" * 45)
    logger.info("🖼️ BOT KOMPRES GAMBAR DIMULAI")
    logger.info(f"🔀 Mode Awal: {GLOBAL_BOT_MODE}")
    logger.info("🌐 Bahasa: Indonesia")
    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.get_me()
    logger.info(f"🤖 Bot: @{me.username}")
    logger.info(f"🆔 ID: {me.id}")
    logger.info("=" * 45)
    logger.info("✅ Bot sedang berjalan...")
    logger.info("🔑 Perintah admin: REDIRECT (nyalakan) | REVERSE (matikan)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
