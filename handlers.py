import json
import logging
import time

import config
import redis
import telebot

log = logging.getLogger(__name__)
bot = telebot.TeleBot(config.API_TOKEN)
r = redis.Redis.from_url(config.REDIS_URI)

HELP = """
/start - shows help message
/help - shows help message
/new title\n
    description of task
/tasks (shows all tasks by default)
/tasks me
"""


class Status:
    TODO = 'TODO'
    DO = 'DO'  # in progress
    DONE = 'DONE'
    ALL = (TODO, DO, DONE)


@bot.message_handler(commands=['do'])
def do(message):
    task = change_status_task(message, status=Status.DO)
    return bot.reply_to(message, f'''Title: {task["title"]}
Status: {task["status"]}
Assignee: {task["assignee"]}
Description:
{task["description"]}''')


@bot.message_handler(commands=['done'])
def done(message):
    task = change_status_task(message, status=Status.DONE)
    return bot.reply_to(message, f'''Title: {task["title"]}
Status: {task["status"]}
Assignee: {task["assignee"]}
Description:
{task["description"]}''')


def change_status_task(message, status):

    assert status in Status.ALL

    _, index = message.text.strip().split()
    index = int(index) - 1
    task = r.lindex(f'/tasks/chat_id/{message.chat.id}', index)

    if task is None:
        return 'No task with such id.'

    task = json.loads(task.decode())
    task['status'] = status
    task['modified'] = time.time()
    task['assignee_id'] = message.from_user.id
    task['assignee'] = message.from_user.username

    r.lset(f'/tasks/chat_id/{message.chat.id}',
           index, json.dumps(task).encode())

    return task


@bot.message_handler(commands=['new'])
def new(message):
    msg = message.text.replace('/new', '', 1)
    args = msg.split('\n', 1)
    if len(args) == 2:
        title, description = msg.split('\n', 1)
    else:
        title, description = msg, ''
    timestamp = time.time()
    task = {
        'title': title,
        'description': description,
        'created': timestamp,
        'modified': timestamp,
        'status': Status.TODO,
        'assignee': None,  # task will be assigned, when someone take it
        'assignee_id': None,
    }
    r.lpush(f'/tasks/chat_id/{message.chat.id}', json.dumps(task).encode())
    return bot.reply_to(message, 'Ok')


@bot.message_handler(commands=['tasks'])
def get_tasks(message):
    # can be passed as a parameter
    limit = 10
    tasks = map(
        json.loads,
        map(
            lambda e: e.decode(),
            r.lrange(
                f'/tasks/chat_id/{message.chat.id}', 0, limit)
        )
    )
    response = '\n'.join(
        [f'{i}. {task["status"]} {task["title"]} - {task["description"][:16]}'
         for i, task in enumerate(tasks, start=1)]
    )
    return bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['task'])
def get_task(message):
    _, index = message.text.strip().split()
    index = int(index) - 1
    task = r.lindex(f'/tasks/chat_id/{message.chat.id}', index)
    if task is None:
        return bot.reply_to(message, 'No task with such id')
    task = json.loads(task.decode())
    return bot.reply_to(message, f'''Title: {task["title"]}
Status: {task["status"]}
Created: {task["created"]}
Modified: {task["modified"]}
Assignee: {task["assignee"]}
Assignee id: {task["assignee_id"]}
Description:
{task["description"]}''')


@bot.message_handler(commands=['help'])
def help_msg(message):
    return bot.reply_to(message, HELP)


@bot.message_handler(commands=['start'])
def start(message):
    return bot.reply_to(message, 'Here will be start message')
