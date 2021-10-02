import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from config import TOKEN
from awsfunc import AwsApi
import sqlite3
import time

ROUTE, MANAGE_ACCOUNT, ADD_ACCOUNT, CHOOSE_ACCOUNT, CHOOSE_COUNTRY, CHOOSE_MODLE, CHOOSE_DISK_SIZE, CHOOSE_QUANTITY, SUBMIT = range(9)
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

def account_filter(update, context):
    query = update.callback_query
    query.answer()
    keyboard = []
    conn = sqlite3.connect('awsbot.sqlite3')
    cursor = conn.cursor()
    cursor.execute("select * from accounts ORDER BY names")#未实现
    users = cursor.fetchall()
    conn.close()
    for i in users:
        users_list = [InlineKeyboardButton(i[1], callback_data=str(i[1]))]
        keyboard.append(users_list)
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="选择账户",
        reply_markup=reply_markup
    )
    return MANAGE_ACCOUNT

def account_info(update,context):
    query = update.callback_query
    query.answer()
    keyboard = []
    account_name = update.callback_query.data
    context.user_data['account_name'] = account_name
    conn = sqlite3.connect('awsbot.sqlite3')
    #未实现
    return CHOOSE_ACCOUNT

def choose_account(update,context):
    query = update.callback_query
    query.answer()
    keyboard = []
    choose = update.callback_query.data
    account_name = context.user_data['account_name']
    if choose=='OK':
        



def add_account(update,context):
    pass#增加user列并与user——id绑定

