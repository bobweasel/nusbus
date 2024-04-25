from contextlib import asynccontextmanager
import telegram
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    filters
)
from telegram import (
    BotCommand
)
from functions import (
#     update_check,
#     update_check1,
#     post_scheduling,
#     invalidate_match,
#     set_timer, unset,
#     forward,
    conversation,
    error_handler,
#     show_group_id,
#     echo
)
import os
import datetime as dt
# from tg_bot.bot import Bots
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response

load_dotenv()

"""
Simple Bot to reply to Telegram messages taken from the python-telegram-bot examples.

debugging locally?
https://github.com/tdlib/telegram-bot-api

add token to environment
procfile worker?
"""

PORT = int(os.environ.get('PORT', '8443'))

toke = 'test'  # alt local bot
# toke = 'main'

environ = os.environ.get('environ') or ''
if 'prod' in environ:
    toke = 'main'

# https://api.telegram.org/bot<token>/getUpdates
# https://docs.python-telegram-bot.org/en/stable/examples.customwebhookbot.html
# https://www.freecodecamp.org/news/how-to-build-and-deploy-python-telegram-bot-v20-webhooks/
# https://github.com/hsdevelops/cron-telebot/blob/main/main.py
# https://github.com/orgs/vercel/discussions/2769


def main(token=None):
    """run"""
    async def post_init(application: Application) -> None:
        command = [BotCommand("help", "view help"),
                   BotCommand("bus", "see available services"),
                   BotCommand("bus_svc", "see available services & routes"),
                   BotCommand("stops", "see stops"),
                   BotCommand("next", "see next bus at a stop"),
                   ]
        await application.bot.set_my_commands(command)

    app = Application.builder().token(token).post_init(post_init).build()

    # app.add_handler(forward_handler)
    app.add_handler(conversation)  # contains start, must be last

    # on noncommand i.e. message - echo the message on Telegram
    # app.add_handler(MessageHandler(filters.TEXT, echo))  # & ~Filters.command  Filters.chat_type.private
    # catch everything else, outside conversation to not reenter

    # log all errors
    app.add_error_handler(error_handler)

    return app


def start(port, token):
    app = main(token)
    # Start the Bot
    if environ == 'prod_vercel':

        app.read_timeout(7).get_updates_read_timeout(42)
        @asynccontextmanager
        async def lifespan(_: FastAPI):
            await app.bot.setWebhook(os.environ['webhook'] + token)
            async with app:
                await app.start()
                yield
                await app.stop()

        # Initialize FastAPI app (similar to Flask)
        app = FastAPI(lifespan=lifespan)
    elif environ == 'local_prod':
        # nginx
        app.run_polling()
        pass
    else:
        app.run_polling()  # run locally

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.


if __name__ == '__main__':
    TOKEN = os.environ['bot']
    start(PORT, token=TOKEN)
