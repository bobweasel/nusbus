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

async def post_init(application: Application) -> None:
    command = [BotCommand("help", "view help"),
               BotCommand("bus", "see available services"),
               BotCommand("bus_svc", "see available services & routes"),
               BotCommand("stops", "see stops"),
               BotCommand("next", "see next bus at a stop"),
               ]
    await application.bot.set_my_commands(command)


def main(port, token=None, bot=None):
    """run"""
    app = Application.builder().token(token).post_init(post_init).build()

    # app.add_handler(forward_handler)
    app.add_handler(conversation)  # contains start, must be last

    # on noncommand i.e. message - echo the message on Telegram
    # app.add_handler(MessageHandler(filters.TEXT, echo))  # & ~Filters.command  Filters.chat_type.private
    # catch everything else, outside conversation to not reenter

    # log all errors
    app.add_error_handler(error_handler)

    if 'prod_' in environ:
        app.run_webhook(listen="0.0.0.0",
                        port=int(port),
                        url_path=token,
                        webhook_url=os.environ['webhook'] + token)
    else: # elif environ == 'local_prod':
        app.run_polling()  # run locally

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.


if __name__ == '__main__':
    TOKEN = os.environ['bot']
    # BOT = Bots.get(toke)
    main(PORT, token=TOKEN)
