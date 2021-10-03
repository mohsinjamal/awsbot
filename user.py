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
        [InlineKeyboardButton("1.选择账号", callback_data=str('账号')),
         InlineKeyboardButton("2.开机", callback_data=str('开机'))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        'Hi 这里是 @GanFan_aws_bot\n目前只开发了开ec2功能（\nby:@QDistinction',
        reply_markup=reply_markup
    )
    return ROUTE

def account_filter(update, context):
    query = update.callback_query
    query.answer()
    keyboard = []
    conn = sqlite3.connect('awsbot.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM accounts WHERE userid=?", (user_id,))
    users = cursor.fetchall()
    conn.close()
    for i in users:
        users_list = [InlineKeyboardButton(i[1], callback_data=str(i[1]))]
        keyboard.append(users_list)
    keyboard.append("InlineKeyboardButton('添加账号', callback_data='添加账号'")
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="选择账户",
        reply_markup=reply_markup
    )
    return MANAGE_ACCOUNT

def account_info(update,context):
    query = update.callback_query
    query.answer()
    keyboard = [InlineKeyboardButton("选定", callback_data="选定"), InlineKeyboardButton("取消", callback_data="取消"), InlineKeyboardButton("删除账号", callback_data="删除账号")]
    account_name = update.callback_query.data
    if account_name == '添加账号':
        add_account()
    else:
        context.user_data['account_name'] = account_name
        conn = sqlite3.connect('awsbot.sqlite3')
        cursor = conn.cursor()
        result = cursor.execute("SELECT key_id,key FROM accounts where userid=? and name='?'", (user_id, account_name,))
        key_id = result[0]
        key = result[1]
        Api = AwsApi(key_id, key)
        quota = Api.get_service_quota()
        if quota:
            query.edit_message_text(
                text="无法查询账户配额呢！（你号没了\n当前回话已结束\n请重新使用/start发起会话"
            )
            return ConversationHandler.END
        else:
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                text=f"当前帐号配额：{quota}\n是否选定此账号作为本次开机账号？",
                reply_markup=reply_markup
            )
            return CHOOSE_ACCOUNT

def choose_account(update,context):
    query = update.callback_query
    query.answer()
    keyboard = []
    choose = update.callback_query.data
    account_name = context.user_data['account_name']
    if choose=='选定':
        account = account_name
    elif choose=='取消':
        return 
    elif choose =='删除账号':
        del_account(account_name)

def add_account(update,context):
    #增加user列并与user_id绑定
    user_id = update.message.from_user.id

def del_account(account_name):
    pass

