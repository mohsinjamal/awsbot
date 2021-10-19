import sqlite3
import time

import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler

from awsfunc import AwsApi
from config import TOKEN

ROUTE, MANAGE_ACCOUNT, ADD_ACCOUNT_STEP1, ADD_ACCOUNT_STEP2, ADD_ACCOUNT_STEP3, CHOOSE_ACCOUNT, CREATE_ROUTE, CHOOSE_REGION, CHOOSE_MODLE, CHOOSE_DISK_SIZE, CHOOSE_OS, CHOOSE_QUANTITY, CHOOSE_TYPE, SUBMIT = range(14)
bot = telegram.Bot(token=TOKEN)


def start(update, context):
    global user_id
    user_id = update.message.from_user.id
    global Selected_modle_name, Selected_region_name, Selected_disk_size, Selected_os, Selected_quantity, Selected_type
    Selected_modle_name = 't2.micro'
    Selected_type = 'x86'
    Selected_region_name = 'us-east-2'
    Selected_disk_size = int(8)
    Selected_os = 'ubuntu 18.04'
    Selected_quantity = int(1)
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
    global Api
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

def create_route(update, context):
    query = update.callback_query
    query.answer()
    try:
        str(Selected_account_name)
        keyboard = [
            [InlineKeyboardButton('选择架构', callback_data=str('选择架构')),
             InlineKeyboardButton('实例类型', callback_data=str('实例类型'))],
            [InlineKeyboardButton('开机区域', callback_data=str('开机区域')),
             InlineKeyboardButton('磁盘大小', callback_data=str('磁盘大小'))],
            [InlineKeyboardButton('选择镜像', callback_data=str('选择镜像')),
             InlineKeyboardButton('开机数量', callback_data=str('开机数量'))],
            [InlineKeyboardButton('检查无误，确认开机', callback_data=str('开机'))]
        ]
        global create_reply_markup
        create_reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text=f'您正在 开机 页面\n \n当前选中账号={Selected_account_name}\n\n以下为开机信息(预设)\n\n实例类型={Selected_modle_name}\n实例区域={Selected_region_name}\n架构={Selected_type}\n磁盘大小={Selected_disk_size}\n系统镜像={Selected_os}\n数量={Selected_quantity}',
            reply_markup=create_reply_markup
        )
        return CREATE_ROUTE
    except NameError:
        query.edit_message_text(text='您还未选择账号，0.3s后将返回主页.....')
        time.sleep(0.2)
        keyboard = [
            [InlineKeyboardButton("1.选择账号", callback_data=str('账号')),
             InlineKeyboardButton("2.开机", callback_data=str('开机'))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text='Hi 这里是 @GanFan_aws_bot\n目前只开发了开ec2功能（支持arm\nby:@QDistinction',
            reply_markup=reply_markup
        )
        return ROUTE

def choose_country(update, context):
    query = update.callback_query
    query.answer()
    global Api
    Api = AwsApi(key_id, key)
    Api.get_describe_regions()
    keyboard = []
    tmp=[]
    n=0
    for i in Api.region_list:
        if n<2:
            tmp.append(InlineKeyboardButton(i, callback_data=str(i)))
            n=n+1
        else:
            keyboard.append(tmp)
            n=1
            tmp = []
            tmp.append(InlineKeyboardButton(i, callback_data=str(i)))
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="选择区域\n未显示即为不支持",
        reply_markup=reply_markup
    )
    return CHOOSE_REGION

def choose_country_exec(update, context):
    global Selected_region_name
    Selected_region_name = update.callback_query.data
    query = update.callback_query
    query.answer()
    query.edit_message_text(text='开机区域 更新成功\n0.3s后返回 开机信息 页面')
    time.sleep(0.2)
    query.edit_message_text(
        text=f'您正在 开机 页面\n \n当前选中账号={Selected_account_name}\n\n以下为开机信息(预设)\n\n实例类型={Selected_modle_name}\n实例区域={Selected_region_name}\n架构={Selected_type}\n磁盘大小={Selected_disk_size}\n系统镜像={Selected_os}\n数量={Selected_quantity}',
        reply_markup=create_reply_markup
    )
    return CREATE_ROUTE

def choose_modle(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton("t2.micro", callback_data=str('t2.micro')),
         InlineKeyboardButton("t3.micro", callback_data=str('t3.micro'))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text="选择实例类型\n\nps:其他类型请直接输入",
        reply_markup=reply_markup
    )
    return CHOOSE_MODLE

def choose_modle_exec_1(update,context):
    query = update.callback_query
    query.answer()
    global Selected_modle_name
    Selected_modle_name = update.callback_query.data
    query.edit_message_text(text='实例类型 更新成功\n0.3s后返回 开机信息 页面')
    time.sleep(0.2)
    query.edit_message_text(
        text=f'您正在 开机 页面\n \n当前选中账号={Selected_account_name}\n\n以下为开机信息(预设)\n\n实例类型={Selected_modle_name}\n实例区域={Selected_region_name}\n架构={Selected_type}\n磁盘大小={Selected_disk_size}\n系统镜像={Selected_os}\n数量={Selected_quantity}',
        reply_markup=create_reply_markup
    )
    return CREATE_ROUTE

def choose_modle_exec_2(update, context):
    global Selected_modle_name
    Selected_modle_name = update.message.text
    update.message.reply_text(text='实例类型 更新成功\n0.3s后返回 开机信息 页面')
    time.sleep(0.2)
    update.message.reply_text(
        text=f'您正在 开机 页面\n \n当前选中账号={Selected_account_name}\n\n以下为开机信息(预设)\n\n实例类型={Selected_modle_name}\n实例区域={Selected_region_name}\n架构={Selected_type}\n磁盘大小={Selected_disk_size}\n系统镜像={Selected_os}\n数量={Selected_quantity}',
        reply_markup=create_reply_markup
    )
    return CREATE_ROUTE

def choose_disk_size(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text='请输入磁盘大小 单位：GB')
    return CHOOSE_DISK_SIZE

def choose_disk_size_exec(update, context):
    try:
        global Selected_disk_size
        Selected_disk_size = int(update.message.text)
        update.message.reply_text(text='磁盘大小 更新成功\n0.3s后返回 开机信息 页面')
        time.sleep(0.2)
        update.message.reply_text(
            text=f'您正在 开机 页面\n \n当前选中账号={Selected_account_name}\n\n以下为开机信息(预设)\n\n实例类型={Selected_modle_name}\n实例区域={Selected_region_name}\n架构={Selected_type}\n磁盘大小={Selected_disk_size}\n系统镜像={Selected_os}\n数量={Selected_quantity}',
            reply_markup=create_reply_markup
         )
        return CREATE_ROUTE
    except ValueError:
        update.message.reply_text(text='请正确输入磁盘大小 ps：数字！！！\n0.3s后返回 开机信息 页面')
        time.sleep(0.2)
        update.message.reply_text(
            text=f'您正在 开机 页面\n \n当前选中账号={Selected_account_name}\n\n以下为开机信息(预设)\n\n实例类型={Selected_modle_name}\n实例区域={Selected_region_name}\n架构={Selected_type}\n磁盘大小={Selected_disk_size}\n系统镜像={Selected_os}\n数量={Selected_quantity}',
            reply_markup=create_reply_markup
         )
        return CREATE_ROUTE

def choose_quantity(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text='请输入数量 必须为数字')
    return CHOOSE_QUANTITY

def choose_quantity_exec(update, context):
    try:
        global Selected_quantity
        Selected_quantity = int(update.message.text)
        update.message.reply_text(text='磁盘大小 更新成功\n0.3s后返回 开机信息 页面')
        time.sleep(0.2)
        update.message.reply_text(
            text=f'您正在 开机 页面\n \n当前选中账号={Selected_account_name}\n\n以下为开机信息(预设)\n\n实例类型={Selected_modle_name}\n实例区域={Selected_region_name}\n架构={Selected_type}\n磁盘大小={Selected_disk_size}\n系统镜像={Selected_os}\n数量={Selected_quantity}',
            reply_markup=create_reply_markup
        )
        return CREATE_ROUTE
    except ValueError:
        update.message.reply_text(text='磁盘大小 更新失败\n0.3s后返回 开机信息 页面')
        time.sleep(0.2)
        update.message.reply_text(
            text=f'您正在 开机 页面\n \n当前选中账号={Selected_account_name}\n\n以下为开机信息(预设)\n\n实例类型={Selected_modle_name}\n实例区域={Selected_region_name}\n架构={Selected_type}\n磁盘大小={Selected_disk_size}\n系统镜像={Selected_os}\n数量={Selected_quantity}',
            reply_markup=create_reply_markup
        )
        return CREATE_ROUTE

def choose_os(update, context):
    query = update.callback_query
    query.answer()
    '''
    keyboard = [
        [InlineKeyboardButton('Centos 7', callback_data=str('Centos 7')),
         InlineKeyboardButton('Ubuntu 18.04', callback_data=str('Ubuntu 18.04'))],
        [InlineKeyboardButton('Windows Server 2019', callback_data=str('Windows Server 2019'))]
    ]
    '''
    keyboard = [InlineKeyboardButton('Ubuntu 18.04', callback_data=str('Ubuntu 18.04'))]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text='选一个?',
        reply_markup=reply_markup
    )
    return CHOOSE_OS

def choose_os_exec(update, context):
    query = update.callback_query
    query.answer()
    global Selected_os
    Selected_os = update.callback_query.data
    query.edit_message_text(text='系统镜像 更新成功\n0.3s后返回 开机信息 页面')
    time.sleep(0.2)
    query.edit_message_text(
        text=f'您正在 开机 页面\n \n当前选中账号={Selected_account_name}\n\n以下为开机信息\n\n实例类型={Selected_modle_name}\n实例区域={Selected_region_name}\n架构={Selected_type}\n磁盘大小={Selected_disk_size}\n系统镜像={Selected_os}\n数量={Selected_quantity}',
        reply_markup=create_reply_markup
    )
    return CREATE_ROUTE



def submit(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text='我明白了，正在开机\n\n（若数量较多请稍等几分钟唔')
    Api.region = Selected_region_name
    Api.start()
    instance_list = []
    for n in range(Selected_quantity):
        status = Api.ec2_create_instances(Selected_modle_name, disk_size=Selected_disk_size, _type=Selected_type)
        if not status:
            query.edit_message_text(text='创建失败唔')
            return ConversationHandler.END
        else:
            for num in range(20):
                if Api.get_instance(Api.instance_id):
                    instance_list.append(f'实例ID: {Api.instance_id}, 实例IP: {Api.ip},')
                    break
    text = ''
    for i in instance_list:
        text = text+i+'\n'
    query.edit_message_text(
        text= f'{text}\n\n\n密码均为 Gan@Fan_aws!bot\n\n\n如遇密码不正确就等下再试吧'
    )

def choose_type(update, context):
    query = update.callback_query
    query.answer()
    keyboard = [
        [InlineKeyboardButton('X86', callback_data=str('x86')),
         InlineKeyboardButton('arm', callback_data=str('arm'))]
    ]
    reply = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        text='选一个?',
        reply_markup=reply
    )
    return CHOOSE_TYPE

def choose_type_exec(update, context):
    query = update.callback_query
    query.answer()
    global Selected_type
    Selected_type = update.callback_query.data
    query.edit_message_text(text='系统架构 更新成功\n0.3s后返回 开机信息 页面')
    time.sleep(0.2)
    query.edit_message_text(
        text=f'您正在 开机 页面\n \n当前选中账号={Selected_account_name}\n\n以下为开机信息\n\n实例类型={Selected_modle_name}\n实例区域={Selected_region_name}\n架构={Selected_type}\n磁盘大小={Selected_disk_size}\n系统镜像={Selected_os}\n数量={Selected_quantity}',
        reply_markup=create_reply_markup
    )
    return CREATE_ROUTE
    
    
def cancel(update, context):
    update.message.reply_text('回话已结束， /start重新发起')
    return ConversationHandler.END



start_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            ROUTE: [
                CommandHandler('start', start),
                CallbackQueryHandler(account_filter, pattern='^' + str('账号') + '$'),
                CallbackQueryHandler(create_route, pattern='^' + str('开机') + '$'),
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
            ],
            CREATE_ROUTE: [
                CommandHandler('start', start),
                CallbackQueryHandler(choose_type, pattern='^'+str('选择架构')+ '$'),
                CallbackQueryHandler(choose_country, pattern='^'+str('开机区域')+ '$'),
                CallbackQueryHandler(choose_modle, pattern='^'+str('实例类型')+ '$'),
                CallbackQueryHandler(choose_disk_size, pattern='^' + str('磁盘大小') + '$'),
                CallbackQueryHandler(choose_quantity, pattern='^' + str('开机数量') + '$'),
                CallbackQueryHandler(choose_os, pattern='^'+str('选择镜像')+ '$'),
                CallbackQueryHandler(submit, pattern='^'+str('开机')+ '$'),
            ],
            CHOOSE_REGION: [
                CommandHandler('start', start),
                CallbackQueryHandler(choose_country_exec, pattern='.*?')
            ],
            CHOOSE_MODLE: [
                CommandHandler('start', start),
                CallbackQueryHandler(choose_modle_exec_1, pattern='.*?'),
                MessageHandler(Filters.text, choose_modle_exec_2)
            ],
            CHOOSE_DISK_SIZE: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, choose_disk_size_exec)
            ],
            CHOOSE_OS: [
                CommandHandler('start', start),
                CallbackQueryHandler(choose_os_exec, pattern='.*?')
            ],
            CHOOSE_QUANTITY: [
                CommandHandler('start', start),
                MessageHandler(Filters.text, choose_quantity_exec)
            ],
            CHOOSE_TYPE: [
                CommandHandler('start', start),
                CallbackQueryHandler(choose_type_exec, pattern='.*?')
            ]
         #   ConversationHandler.TIMEOUT: [MessageHandler(Filters.all, timeout)],
        },
        conversation_timeout=300,
        fallbacks=[CommandHandler('cancel', cancel)]
    )