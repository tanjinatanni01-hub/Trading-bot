import logging
import base64
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8773917667:AAGHpAlqaiYxIO-gJsz4kNRBIQXijukJUME"
GEMINI_API_KEY = "AIzaSyCoNPG1pju24s-a2inTl0aKFzdLGAXWQys"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY

SMC_PROMPT = "You are a professional SMC trading analyst. Analyze this chart image and respond ONLY in Bangla language. Use this format:\n\n1. MARKET STRUCTURE\n- Trend (Bullish/Bearish/Ranging):\n- BOS detected:\n- ChoCH detected:\n\n2. LIQUIDITY\n- Buy Side Liquidity (BSL):\n- Sell Side Liquidity (SSL):\n- Equal Highs/Lows:\n- Stop Hunt occurred:\n- Next Liquidity Target:\n\n3. ORDER BLOCKS\n- Bullish OB:\n- Bearish OB:\n- Strongest OB:\n\n4. FAIR VALUE GAP\n- Bullish FVG:\n- Bearish FVG:\n\n5. PREMIUM AND DISCOUNT\n- Current zone:\n- OTE zone:\n\n6. TRADE SETUP\n- Signal (BUY/SELL/WAIT):\n- Entry:\n- Stop Loss:\n- TP1:\n- TP2:\n- TP3:\n- Risk Reward:\n- Confidence 1 to 10:"

QUICK_PROMPT = "You are an SMC trader. Analyze this chart image and respond ONLY in Bangla in 5 lines:\n1. Trend:\n2. Liquidity:\n3. Signal BUY or SELL:\n4. Entry and SL:\n5. TP:"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Full SMC Analysis", callback_data="full")],
        [InlineKeyboardButton("Quick Signal", callback_data="quick")],
    ]
    await update.message.reply_text(
        "SMC Trading Analysis Bot\nSend chart screenshot.\nChoose mode:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "full":
        context.user_data["mode"] = "full"
        await query.edit_message_text("Full SMC Analysis mode ON. Send chart screenshot.")
    elif query.data == "quick":
        context.user_data["mode"] = "quick"
        await query.edit_message_text("Quick Signal mode ON. Send chart screenshot.")
    elif query.data == "change":
        keyboard = [
            [InlineKeyboardButton("Full SMC Analysis", callback_data="full")],
            [InlineKeyboardButton("Quick Signal", callback_data="quick")],
        ]
        await query.edit_message_text("Choose mode:", reply_markup=InlineKeyboardMarkup(keyboard))

async def analyze_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode", "full")
    prompt = QUICK_PROMPT if mode == "quick" else SMC_PROMPT
    await update.message.reply_text("Analyzing chart, please wait...")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        async with httpx.AsyncClient() as client:
            img_response = await client.get(file.file_path)
            image_data = base64.b64encode(img_response.content).decode("utf-8")
        payload = {
            "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}]}],
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
            [InlineKeyboardButton("Analyze another chart", callback_data=mode)],
            [InlineKeyboardButton("Change mode", callback_data="change")],
        ]
        await update.message.reply_text("Send another chart?", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Analysis failed. Use /start to try again.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Full SMC Analysis", callback_data="full")],
        [InlineKeyboardButton("Quick Signal", callback_data="quick")],
    ]
    await update.message.reply_text("Send chart screenshot. Choose mode:", reply_markup=InlineKeyboardMarkup(keyboard))

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
