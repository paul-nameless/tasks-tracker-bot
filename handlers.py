import logging
import time

import config
import redis
import telebot
from utils import decode, encode

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
    if task:
        return bot.reply_to(message, f'''Title: {task["title"]}
Status: {task["status"]}
Assignee: {task["assignee"]}
Description:
{task["description"]}''')


@bot.message_handler(commands=['todo'])
def todo(message):
    task = change_status_task(message, status=Status.TODO)
    if task:
        return bot.reply_to(message, f'''Title: {task["title"]}
Status: {task["status"]}
Assignee: {task["assignee"]}
Description:
{task["description"]}''')


@bot.message_handler(commands=['done'])
def done(message):
    task = change_status_task(message, status=Status.DONE)
    if task:
        return bot.reply_to(message, f'''Title: {task["title"]}
Status: {task["status"]}
Assignee: {task["assignee"]}
Description:
{task["description"]}''')


def change_status_task(message, status):

    assert status in Status.ALL

    _, task_id = message.text.strip().split()
    task = r.hget(f'/tasks/chat_id/{message.chat.id}', task_id)
    if task is None:
        bot.reply_to(message, 'No task with such id')
        return None

    task = decode(task)
    task['status'] = status
    task['modified'] = time.time()
    task['assignee_id'] = message.from_user.id
    task['assignee'] = f'@{message.from_user.username}'

    r.hset(f'/tasks/chat_id/{message.chat.id}', task_id, encode(task))
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

    task_id = r.incr(f'/tasks/chat_id/{message.chat.id}/last_task_id')

    task = {
        'title': title,
        'description': description,
        'created': timestamp,
        'modified': timestamp,
        'status': Status.TODO,
        'assignee': '',  # task will be assigned, when someone take it
        'assignee_id': '',
    }

    r.hset(f'/tasks/chat_id/{message.chat.id}', task_id, encode(task))

    return bot.reply_to(message, 'Ok')


@bot.message_handler(commands=['tasks'])  # /tasks [opt: task_id] [opt: limit]
def get_tasks(message):

    try:
        _, offset, limit = message.text.strip().split()
        offset = int(offset)
        limit = int(limit)
    except Exception:
        print("Error!!! /tasks [required: offset] [required: limit]")
        bot.send_message(
            message.chat.id,
            "Error!!! /tasks [required: offset] [required: limit]"
        )
        return

    last_task_id = r.get(
        f'/tasks/chat_id/{message.chat.id}/last_task_id')
    last_task_id = int(last_task_id) - offset

    keys = [last_task_id - i for i in range(limit) if last_task_id - i > 0]

    if keys:
        tasks = r.hmget(f'/tasks/chat_id/{message.chat.id}', *keys)

        response = '\n'.join(
            [f'{task_id}. {task["status"]} {task["title"]}'
             for task_id, task in zip(keys, map(decode, filter(None, tasks)))]
        )
    else:
        response = "No tasks for such offset."

    return bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['task'])
def get_task(message):
    _, task_id = message.text.strip().split()
    task = r.hget(f'/tasks/chat_id/{message.chat.id}', task_id)

    if task is None:
        return bot.reply_to(message, 'No task with such id')

    task = decode(task)
    return bot.reply_to(message, f'''Task id: {task_id}
Title: {task["title"]}
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
