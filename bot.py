from contextlib import asynccontextmanager
from http import HTTPStatus
from telegram import Update
from telegram.ext import Application, CommandHandler
from telegram.ext._contexttypes import ContextTypes
from fastapi import FastAPI, Request, Response
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize python telegram bot
ptb = (
        Application.builder()
        .token(os.environ.get('bot'))
        .read_timeout(7)
        .get_updates_read_timeout(42)
        .build()
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    # await ptb.bot.setWebhook(f"{os.environ.get('webhook')}") # replace <your-webhook-url>
    async with ptb:
        await ptb.start()
        yield
        await ptb.stop()

# Initialize FastAPI app (similar to Flask)
app = FastAPI(lifespan=lifespan)

@app.post("/")
async def process_update(request: Request):
    req = await request.json()
    update = Update.de_json(req, ptb.bot)
    await ptb.process_update(update)
    return Response(status_code=HTTPStatus.OK)

# Example handler
async def start(update, _: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text("starting...")

ptb.add_handler(CommandHandler("start", start))
uvicorn.run(app, host="0.0.0.0", port=8443)


