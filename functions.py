from http.client import HTTPSConnection
from base64 import b64encode

import html
import json
import traceback
import requests
import os
from pprint import pprint

from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
)

from functools import wraps


# https://suibianp.github.io/nus-nextbus-new-api/#/default/GetShuttleService

def user(func):
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        if 'handle' not in context.bot_data:
            context.bot_data['handle'] = Handle()
        return await func(update, context, *args, **kwargs)

    return wrapped


class Handle:

    _cache = {}

    def _get_headers(self):
        def basic_auth(username, password):
            token = b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
            return f'Basic {token}'

        username = os.environ['user']
        password = os.environ['pass']

        return {
            'accept': 'application/json',
            'Authorization': basic_auth(username, password),
        }

    def post_req(self, endpoint, param=None):
        response = requests.get(f'https://nnextbus.nus.edu.sg/{endpoint}',
                                params=param,
                                headers=self._get_headers())

        # pprint(response.json())
        return response

    def busstop(self):
        endpoint = 'BusStops'
        if 'stops' not in self._cache:
            r = self.post_req(endpoint)
            self._cache['stops_res'] = rs = r.json()['BusStopsResult']['busstops']
            self._cache['stops'] = {f'{x["name"]}': x for x in rs}
            self._cache['stops_data'] = r
        return self._cache['stops_data']

    def pickups(self, route_code):
        # Get all pickup points of a specified route
        endpoint = 'PickupPoint'
        params = {
            "route_code": route_code
        }
        return self.post_req(endpoint, params)

    def service(self, busstopname):
        # Get all oncoming shuttle bus services at a specified stop
        endpoint = 'ShuttleService'
        params = {
            "busstopname": busstopname
        }
        r = self.post_req(endpoint, params)
        # if 'routes' not in self.__cache:
        #     rs = r.json()['ServiceDescriptionResult']['ServiceDescription']
        #     self._cache['routes'] = {f'{x["Route"]}': x for x in rs}
        return r

    def activebus(self, route_code):
        endpoint = 'ActiveBus'
        params = {
            "route_code": route_code
        }
        return self.post_req(endpoint, params)

    def BusLocation(self, veh_plate):
        endpoint = 'BusLocation'
        params = {
            "veh_plate": veh_plate
        }
        return self.post_req(endpoint, params)

    def RouteMinMaxTime(self, route_code):
        endpoint = 'RouteMinMaxTime'
        params = {
            "route_code": route_code
        }
        return self.post_req(endpoint, params)

    def ServiceDescription(self):
        # get buses and description
        endpoint = 'ServiceDescription'

        if 'routes' not in self._cache:
            r = self.post_req(endpoint)
            self._cache['routes_res'] = rs = r.json()['ServiceDescriptionResult']['ServiceDescription']
            self._cache['routes'] = {f'{x["Route"]}': x for x in rs}
            self._cache['routes_data'] = r
        return self._cache['routes_data']

    def Announcements(self):
        endpoint = 'Announcements'
        return self.post_req(endpoint)

    def publicity(self):
        endpoint = 'publicity'
        return self.post_req(endpoint)

    def TickerTapes(self):
        endpoint = 'TickerTapes'
        return self.post_req(endpoint)

    def CheckPoint(self, route_code):
        endpoint = 'CheckPoint'
        params = {
            "route_code": route_code
        }
        return self.post_req(endpoint, params)


@user
async def get_buses(update, context):  # /bus
    context.bot_data['handle'].ServiceDescription()
    await update.effective_message.reply_text(
        f'<pre>{" ".join(context.bot_data['handle']._cache['routes'].keys())}'
        f'</pre>', parse_mode='HTML')

@user
async def get_buses_route(update, context):  # /bus
    context.bot_data['handle'].ServiceDescription()
    r = context.bot_data['handle']._cache['routes_res']
    s = ""
    for x in r:
        s += f'{x["Route"]}: {x["RouteDescription"]}\n'
    await update.effective_message.reply_text(
        f'<pre>{s}'
        f'</pre>', parse_mode='HTML')


@user
async def get_stops(update, context):  # /bus
    context.bot_data['handle'].busstop()
    r = context.bot_data['handle']._cache['stops_res']
    s = ""
    for x in r:
        s += f'{x["name"]}: {x["LongName"]}\n'
    await update.effective_message.reply_text(
        f'<pre>{s}'
        f'</pre>', parse_mode='HTML')

@user
async def get_next(update, context):  # /bus
    load = update.effective_message.text.split(' ')
    if len(load) != 2:
        await update.effective_message.reply_text(
            f'Use /next with the bus stop name!\ne.g. '
            f'<pre>/next KR-MRT</pre>\n'
            f'Use /stops to get the list of stops.', parse_mode='HTML')
        return
    assert len(load) == 2
    r = context.bot_data['handle'].service(load[1]).json()['ShuttleServiceResult']
    s = f"Stop: {r['caption']}\n"
    print(update)
    print(update.effective_message.date)

    for x in r['shuttles']:
        s += f'{x["name"]}: {x["arrivalTime"]} / {x["nextArrivalTime"]}\n'
    await update.effective_message.reply_text(
        f'<pre>{s}'
        f'</pre>', parse_mode='HTML')


async def error_handler(update, context):
    await process_error(update, context)


async def process_error(update, context):
    """Log Errors caused by Updates.

    https://stackoverflow.com/questions/51423139/python-telegram-bot-flood-control-exceeded
    time out
    """

    # if chat not found run id_init? telegram.error.BadRequest: Chat not found
    err = context.error
    print(f'{type(err)}: {err}')
    print(err.__traceback__)
    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, err, err.__traceback__)
    tb_string = ''.join(tb_list)
    print(tb_string)

    # # logger.warning(f'Update {update} caused error {err=}')
    # if type(err) == telegram.error.TimedOut:
    #     await context.bot.send_message(chat_id=update.effective_message.chat_id,
    #                              text=f"Please try again.")
    #     await report(text=f'Update "{update}" caused error "{err}"')
    #     return
    # if type(err) == telegram.error.Forbidden:
    #     await report(text=f'Update "{update}" caused error "{err}"')
    #     return
    # if type(err) == telegram.error.RetryAfter:
    #     await asyncio.sleep(0.2)
    #     await report(f"{err} {update}")
    #     # context.bot.send_message(chat_id=update.effective_message.chat_id,
    #     #                          text=f"Looks like you are texting too fast! Please retry in "
    #     #                               f"{number_finder(err, decimal=True)[0]} seconds")
    #     return
    #
    # # Log the error before we do anything else, so we can see it even if something breaks.
    # logger.error(msg="Exception while handling an update:", exc_info=err)
    #
    # if update is not None:
    #     print('update')
    #     print(json.dumps(
    #         update.to_dict(), indent=2, ensure_ascii=False))
    # print('chat_data')
    # try:
    #     print(pprint.pformat(context.chat_data))
    # except Exception as e:
    #     print(f'{e=}')
    #     try:
    #         print(context.chat_data)
    #     except Exception as e:
    #         print(f'{e=}')
    # print('user_data')
    # try:
    #     print(pprint.pformat(context.user_data))
    # except Exception as e:
    #     print(f'{e=}')
    #     print(context.user_data)
    #
    # if 'prod' not in os.environ.get('environ', ''):  # if local
    #     return
    #
    # try:
    #     if update is not None:  # called by user, not like job
    #         await report(
    #             text=f'user {helpers.mention_html(update.effective_user.id, update.effective_user.first_name)} \n'
    #                  f'Update "{update}" \n\ncaused error "{err}"',
    #             chat_id=Channels.error)
    # except telegram.error.BadRequest as e:
    #     await report(text=f'error encountered but Bad Request raised while sending! {e}',
    #                  chat_id=Channels.error)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.

    texts = ['An exception was raised while handling an update',
             '<pre>context.chat_data = {}</pre>'.format(html.escape(str(context.chat_data))),
             '<pre>context.user_data = {}</pre>'.format(html.escape(str(context.user_data))),
             '<pre>{}</pre>'.format(html.escape(tb_string))
             ]
    if update is not None:
        texts.insert(1,
                     '<pre>update = {}</pre>'.format(html.escape(json.dumps(
                         update.to_dict(), indent=2, ensure_ascii=False))))

    # Finally, send the message
    # text = '\n\n'.join(texts)
    # if len(text) <= 4096:
    #     await report(chat_id=Channels.error, text='\n\n'.join(texts))
    # else:  # type(e) == telegram.error.BadRequest and str(e) == 'Message is too long'
    #     for t in texts[1:]:
    #         await report(text=t,
    #                      chat_id=Channels.error)


conversation = ConversationHandler(
    entry_points=[
        CommandHandler('bus', get_buses),
        CommandHandler('bus_svc', get_buses_route),
        CommandHandler('stops', get_stops),
        CommandHandler('next', get_next),
    ],
    states={},
    fallbacks=[]
)

if __name__ == '__main__':
    Handle().ServiceDescription()
