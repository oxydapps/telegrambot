import json
import os
import sys
import logging
import telegram
from pprint import pprint
from threading import Thread
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters)


def write_json_conf(data, fp):
    with open(fp, 'w') as file:
        json.dump(data, file, indent=4, separators=(',', ': '), sort_keys=True)


log_level = logging.INFO
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log_level)
logger = logging.getLogger(__name__)

CONF = dict()
BOT_CONF_FP = 'conf_bot.json'

if os.path.isfile(BOT_CONF_FP):
    print(f'"{BOT_CONF_FP}" exists')
    with open(BOT_CONF_FP, 'r') as f:
        CONF.update(json.load(f))
else:
    print(f'Creating new bot config "{BOT_CONF_FP}"')
    write_json_conf(
        dict(token='YOUR_TELEGRAM_TOKEN_HERE'),
        BOT_CONF_FP)
    sys.exit()

TOKEN = CONF['token']
BOT = telegram.Bot(TOKEN)

print('Starting telegram bot...')


def help_view():
    pass


def process_text(text):
    out = os.popen('{} {} "{}"'.format(
        sys.executable,
        'aws_text_check.py',
        text,
    )).read()
    return out


def process_img(fp):
    base_dir = 'predictor'
    bin_fp = os.path.join(base_dir, 'predict.py')
    model_fp = os.path.join(base_dir, 'imagenet_class_index.json')
    out = os.popen('{} {} --path {} --model-path {}'.format(
        sys.executable,
        bin_fp,
        fp,
        model_fp,
    )).read()
    return out


def photo_view(update, context):
    msg = update.message.to_dict()

    tmp_dir = os.path.join('predictor', 'tmp')
    if not os.path.isdir(tmp_dir):
        os.mkdir(tmp_dir)

    file_id = msg.get('photo')[-1]['file_id']
    file_obj = update.message.bot.get_file(file_id)

    img_fp = os.path.join(tmp_dir, f'{file_id}.webp')
    file_obj.download(img_fp)

    update.message.reply_html(process_img(img_fp))
    pprint(msg)


def filter_text(text):
    import string

    result = []

    wordl_list = text.split(' ')
    for word in wordl_list:
        f_word = ''.join([x for x in word if x in string.ascii_letters])
        result.append(f_word)
    return ' '.join(result)


def echo_view(update, context):
    msg = update.message.to_dict()
    msg_type = (msg.get('chat', {}).get('type'))
    text = msg.get('text')
    pprint(msg)
    print(text)



    if any(['dpaste' in text, 'github' in text]):
        update.message.bot.send_message('новый код найден', parse_mode='HTML', quote=True)
    elif 'привет' in msg.get('text'):
        update.message.reply_html('привет человек', parse_mode='HTML', quote=True)

    #это, если бот подключен к чату и можно с собакой передавать ему текст
    # entities = msg.get('entities')
    # if entities:
    #     if entities[0]['type'] == 'mention':
    #         update.message.reply_html(process_text(text)['sentiment'], quote=True)

    # боту в личку писать и он подключается к анализатору aws
    # if msg_type == 'private':
    #     print('TEST')
    #     f_text = filter_text(text)
    #     update.message.reply_html(process_text(f_text))
    #     update.message.reply_html(process_text(f_text)['sentiment'])


def error_view(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "{}" caused error "{}"'.format(update, context.error))


def main():
    """Start the bot."""
    upd = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = upd.dispatcher

    # on different commands - answer in Telegram
    # dp.add_handler(CommandHandler('start', start_view))
    dp.add_handler(CommandHandler('h', help_view))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo_view))
    dp.add_handler(MessageHandler(Filters.photo, photo_view))

    # log all errors
    dp.add_error_handler(error_view)

    def stop_and_restart():
        """Gracefully stop the Updater and replace the current process with a new one"""
        upd.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(update):
        update.message.reply_text('Bot is restarting...')
        Thread(target=stop_and_restart).start()

    dp.add_handler(CommandHandler('r', restart))

    # Start the Bot
    upd.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    upd.idle()


if __name__ == '__main__':
    main()
