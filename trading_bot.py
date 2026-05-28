# -*- coding: utf-8 -*-
import logging
import base64
import os
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8773917667:AAE2nY4-zP0H1WUnL5macvL92wvfYl-ianY"
GEMINI_API_KEY = "AIzaSyCoNPG1pju24s-a2inTl0aKFzdLGAXWQys"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

SMC_PROMPT = (
    "You are a professional Smart Money Concepts (SMC) trading analyst. "
    "Analyze this chart and respond ONLY in Bangla language with this exact format:\n\n"
    "SMC + LIQUIDITY BISHLESHON\n\n"
    "1. MARKET STRUCTURE\n"
    "- Trend:\n"
    "- BOS (Break of Structure):\n"
    "- ChoCH (Change of Character):\n\n"
    "2. LIQUIDITY\n"
    "- Buy Side Liquidity (BSL):\n"
    "- Sell Side Liquidity (SSL):\n"
    "- Equal Highs/Lows:\n"
    "- Stop Hunt hoyeche ki:\n"
    "- Next Liquidity Target:\n\n"
    "3. ORDER BLOCKS\n"
    "- Bullish OB:\n"
    "- Bearish OB:\n"
    "- Strongest OB:\n\n"
    "4. FAIR VALUE GAP\n"
    "- Bullish FVG:\n"
    "- Bearish FVG:\n\n"
    "5. PREMIUM & DISCOUNT\n"
    "- Current zone:\n"
    "- OTE zone:\n\n"
    "6. TRADE SETUP\n"
    "- Signal: BUY / SELL / WAIT\n"
    "- Entry:\n"
    "- Stop Loss:\n"
    "- TP1:\n"
    "- TP2:\n"
    "- TP3:\n"
    "- Risk:Reward:\n"
    "- Confidence (1-10):\n\n"
    "Note: This is analysis only, not financial advice."
)

QUICK_PROMPT = (
    "You are an SMC trader. Analyze this chart and respond ONLY in Bangla in exactly 5 lines:\n"
    "1. Trend:\n"
    "2. Liquidity:\n"
    "3. Signal (BUY/SELL):\n"
    "4. Entry & SL:\n"
    "5. TP:\n"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Full SMC Analysis", callback_data="full")],
        [InlineKeyboardButton("⚡ Quick Signal", callback_data="quick")],
    ]
    await update.message.reply_text(
        "🤖 SMC Trading Analysis Bot\n\n"
        "Chart screenshot pathান - ami bishleshon korbo.\n\n"
        "Mode beche nin:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "full":
        context.user_data["mode"] = "full"
        await query.edit_message_text(
            "✅ Full SMC Analysis mode ON\n\n"
            "📸 Chart screenshot pathান."
        )
    elif query.data == "quick":
        context.user_data["mode"] = "quick"
        await query.edit_message_text(
            "✅ Quick Signal mode ON\n\n"
            "📸 Chart screenshot pathান."
        )
    elif query.data == "change":
        keyboard = [
            [InlineKeyboardButton("📊 Full SMC Analysis", callback_data="full")],
            [InlineKeyboardButton("⚡ Quick Signal", callback_data="quick")],
        ]
        await query.edit_message_text("Mode beche nin:", reply_markup=InlineKeyboardMarkup(keyboard))

async def analyze_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode", "full")
    prompt = QUICK_PROMPT if mode == "quick" else SMC_PROMPT
    await update.message.reply_text("⏳ Bishleshon hocche, wait korun...")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        async with httpx.AsyncClient() as client:
            img_response = await client.get(file.file_path)
            image_data = base64.b64encode(img_response.content).decode("utf-8")

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
                ]
            }],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2048}
        }

        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(GEMINI_URL, json=payload)
            result = response.json()

        analysis = result["candidates"][0]["content"]["parts"][0]["text"]

        if len(analysis) > 4000:
            await update.message.reply_text(analysis[:4000])
            await update.message.reply_text(analysis[4000:])
        else:
            await update.message.reply_text(analysis)

        keyboard = [
            [InlineKeyboardButton("🔄 Arekta chart", callback_data=mode)],
            [InlineKeyboardButton("🔀 Mode change", callback_data="change")],
        ]
        await update.message.reply_text(
            "Arekta chart pathaben?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "❌ Bishleshon e somosya hoyeche.\n"
            "/start diye abar try korun."
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Full SMC Analysis", callback_data="full")],
        [InlineKeyboardButton("⚡ Quick Signal", callback_data="quick")],
    ]
    await update.message.reply_text(
        "📸 Chart screenshot pathান.\nAge mode beche nin:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, analyze_chart))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
