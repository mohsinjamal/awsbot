import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from config import TOKEN
from awsfunc import AwsApi
import sqlite3
import time

ROUTE, MANAGE_ACCOUNT, ADD_ACCOUNT_STEP1, ADD_ACCOUNT_STEP2, ADD_ACCOUNT_STEP3, CHOOSE_ACCOUNT, CHOOSE_COUNTRY, CHOOSE_MODLE, CHOOSE_DISK_SIZE, CHOOSE_QUANTITY, SUBMIT = range(11)
bot = telegram.Bot(token=TOKEN)


def start(update, context):
    global user_id
    user_id = update.message.from_user.id
    print('进入start函数')
    keyboard = [
        [InlineKeyboardButton("1.选择账号", callback_data=str('账号')),
         InlineKeyboardButton("2.开机", callback_data=str('开机'))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        'Hi 这里是 @GanFan_aws_bot\n目前只开发了开ec2功能（支持arm\nby:@QDistinction',
        reply_markup=reply_markup
    )
    return ROUTE

def account_filter(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [[InlineKeyboardButton('添加账号', callback_data=str('添加账号'))]]
    conn = sqlite3.connect('awsbot.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM accounts WHERE userid=?", (user_id,))
    users = cursor.fetchall()
    conn.close()
    for i in users:
        users_list = [InlineKeyboardButton(i[0], callback_data=str(i[0]))]
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
    keyboard = [[InlineKeyboardButton("选定", callback_data=str("选定")), InlineKeyboardButton("取消", callback_data=str("取消")), InlineKeyboardButton("删除账号", callback_data=str("删除账号"))]]
    account_name = update.callback_query.data

    context.user_data['account_name'] = account_name
    conn = sqlite3.connect('awsbot.sqlite3')
    cursor = conn.cursor()
    result = cursor.execute("SELECT key_id,key FROM accounts where userid=? and name=?", (user_id, account_name,))
    result = result.fetchall()
    global key_id, key
    key_id = result[0][0]
    key = result[0][1]
    Api = AwsApi(key_id, key)
    quota = Api.get_service_quota()
    print(quota)
    if quota==False:
        keyboard = [
            [InlineKeyboardButton("取消", callback_data=str("取消")),
             InlineKeyboardButton("删除账号", callback_data=str("删除账号"))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text="无法查询账户配额呢！（你号没了",
            reply_markup=reply_markup
        )
        return CHOOSE_ACCOUNT
    else:
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text=f"当前帐号配额：{quota}\n是否选定此账号作为本次开机账号？",
            reply_markup=reply_markup
        )
        return CHOOSE_ACCOUNT

def add_account_route(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text('请输入账号名称')
    return ADD_ACCOUNT_STEP1

def add_step_1(update, context):
    global newname
    newname = update.message.text
    conn = sqlite3.connect('awsbot.sqlite3')
    cursor = conn.cursor()
    result = cursor.execute("SELECT key_id FROM accounts where userid=? and name=?", (user_id, newname,))
    result = result.fetchone()
    conn.close()
    if result is None:
        update.message.reply_text('请输入key_id')
        return ADD_ACCOUNT_STEP2
    else:
        update.message.reply_text('名称不能重复，请检查后再试\n当前回话已结束，请重启回话')
        return ConversationHandler.END

def add_step_2(update, context):
    global newkeyid
    newkeyid = update.message.text
    update.message.reply_text('请输入key setret')
    return ADD_ACCOUNT_STEP3

def add_step_3(update, context):
    try:
        newsecret = update.message.text
        conn = sqlite3.connect('awsbot.sqlite3')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO accounts VALUES (?, ?, ?, ?)", (user_id, newkeyid, newsecret, newname))
        conn.commit()
        conn.close()
        update.message.reply_text('添加成功,当前会话已结束，请使用 /start')
        print(user_id, newkeyid, newsecret, newname)
        return ConversationHandler.END
    except Exception as e:
        update.message.reply_text(str(e))
        return ConversationHandler.END


def choose_account(update,context):
    query = update.callback_query
    query.answer()
    global Selected_account_name
    Selected_account_name = context.user_data['account_name']
    query.edit_message_text(
        text=f"ok\n当前账号：{Selected_account_name} \n3s后返回主页",
   )
    time.sleep(3)
    keyboard = [
        [InlineKeyboardButton("1.选择账号", callback_data=str('账号')),
         InlineKeyboardButton("2.开机", callback_data=str('开机'))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        'Hi 这里是 @GanFan_aws_bot\n目前只开发了开ec2功能（支持arm\nby:@QDistinction',
        reply_markup=reply_markup
    )
    return ROUTE


def del_account(update,context):
    query = update.callback_query
    query.answer()
    delaccountname = context.user_data['account_name']
    del context.user_data['account_name']
    conn = sqlite3.connect('awsbot.sqlite3')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Accounts WHERE name=? AND userid=?", (delaccountname, user_id))
    conn.commit()
    conn.close()
    query.edit_message_text(
        text="删除成功，当前回话已结束，请使用 /start",
    )
    return ConversationHandler.END


def cancel(update, context):
    update.message.reply_text('回话已结束， /start重新发起')
    return ConversationHandler.END



start_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            ROUTE: [
                CommandHandler('start', start),
                CallbackQueryHandler(account_filter, pattern='^' + str('账号') + '$'),
                CallbackQueryHandler(account_filter, pattern='^' + str('开机') + '$'),
            ],
            MANAGE_ACCOUNT: [
                CommandHandler('start', start),
                CallbackQueryHandler(add_account_route, pattern='^'+str('添加账号')+'$'),
                CallbackQueryHandler(account_info, pattern='.*?')
            ],
            ADD_ACCOUNT_STEP1: [
                CommandHandler('start', start),
                CommandHandler('cancel', cancel),
                MessageHandler(Filters.text, add_step_1)
            ],
            ADD_ACCOUNT_STEP2: [
                CommandHandler('start', start),
                CommandHandler('cancel', cancel),
                MessageHandler(Filters.text, add_step_2)
            ],
            ADD_ACCOUNT_STEP3: [
                CommandHandler('start', start),
                CommandHandler('cancel', cancel),
                MessageHandler(Filters.text, add_step_3)
            ],
            CHOOSE_ACCOUNT: [
                CommandHandler('start', start),
                CallbackQueryHandler(choose_account, pattern='^' + str('选定') + '$'),
                CallbackQueryHandler(account_filter, pattern='^' + str('取消') + '$'),
                CallbackQueryHandler(del_account, pattern='^' + str('删除账号') + '$'),
            ]
         #   ConversationHandler.TIMEOUT: [MessageHandler(Filters.all, timeout)],
        },
        conversation_timeout=300,
        fallbacks=[CommandHandler('cancel', cancel)]
    )