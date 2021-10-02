import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from config import TOKEN
from awsfunc import AwsApi
import sqlite3
import time

ROUTE, ADD_USER, CHOOSE_USER, CHOOSE_COUNTRY, CHOOSE_MODLE, CHOOSE_DISK_SIZE, CHOOSE_QUANTITY, SUBMIT = range(8)
bot = telegram.Bot(token=TOKEN)

def start(update, context):
    print('进入start函数')
    keyboard = [
        [InlineKeyboardButton("管理账号", callback_data=str('管理账号')),
         InlineKeyboardButton("开机", callback_data=str('开机'))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        'Hi 这里是 @GanFan_aws_bot\n目前只开发了开ec2功能，抱歉（\nby:@QDistinction',
        reply_markup=reply_markup
    )
    return ROUTE