import logging
import time
from tempfile import TemporaryFile

from singleton import bot, db
from utils import Status, change_status_task, decode, encode
from validator import arg, status_enum, validate

log = logging.getLogger(__name__)
LIMIT = 10
HELP = """This is simple task manager
/start - shows help message
/help - shows help message
/new title\n
    description of task
/tasks (default show all tasks)
/tasks todo 10
/tasks done 10
/tasks all 5
/export - exports to csv file
/task [task_id] - print detailed info about task by id
/do - mark task status as DO
/done - mark task status as DONE
/todo - mark task status as TODO
"""


@bot.message_handler(commands=['do'])
@validate(task_id=arg(int, required=True))
def do(message, task_id):
    task = change_status_task(message, task_id, status=Status.DO)
    if task:
        return bot.reply_to(message, f'''Title: {task["title"]}
Status: {task["status"]}
Assignee: {task["assignee"]}
Description:
{task["description"]}''')


@bot.message_handler(commands=['todo'])
def todo(message, task_id):
    task = change_status_task(message, task_id, status=Status.TODO)
    if task:
        return bot.reply_to(message, f'''Title: {task["title"]}
Status: {task["status"]}
Assignee: {task["assignee"]}
Description:
{task["description"]}''')


@bot.message_handler(commands=['done'])
@validate(task_id=arg(int, required=True))
def done(message, task_id):
    task = change_status_task(message, task_id, status=Status.DONE)
    if task:
        return bot.reply_to(message, f'''Title: {task["title"]}
Status: {task["status"]}
Assignee: {task["assignee"]}
Description:
{task["description"]}''')


@bot.message_handler(commands=['new'])
def new(message):
    msg = message.text.replace('/new', '', 1)
    args = msg.split('\n', 1)
    if len(args) == 2:
        title, description = msg.split('\n', 1)
    else:
        title, description = msg, ''
    timestamp = time.time()

    task_id = db.incr(f'/tasks/chat_id/{message.chat.id}/last_task_id')

    task = {
        'title': title.strip().capitalize(),
        'description': description,
        'created': timestamp,
        'modified': timestamp,
        'status': Status.TODO,
        'assignee': '',  # task will be assigned, when someone take it
        'assignee_id': '',
    }

    db.hset(f'/tasks/chat_id/{message.chat.id}', task_id, encode(task))

    return bot.reply_to(message, f'Created new task with id {task_id}')


@bot.message_handler(commands=['tasks'])  # /tasks [opt: task_id]
@validate(status=arg(status_enum, Status.TODO), offset=arg(int, 0))
def get_tasks(message, status, offset):
    last_task_id = db.get(
        f'/tasks/chat_id/{message.chat.id}/last_task_id')
    task_id = int(last_task_id) - offset
    tasks = {}

    while task_id > 0 and len(tasks) < LIMIT:
        task, *_ = db.hmget(f'/tasks/chat_id/{message.chat.id}', task_id)
        task_id -= 1
        if not task:
            continue
        task = decode(task)
        if status in Status.ALL and task['status'].upper() != status:
            continue
        tasks[task_id + 1] = task

    if tasks:
        response = '\n'.join(
            [f'{task_id}. {task["status"]} {task["title"]} {task["assignee"]}'
             for task_id, task in tasks.items()]
        )
    else:
        response = f"No tasks for such offset {offset} and status {status}"

    if response:
        return bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['update'])
def update(message):
    msg = message.text.replace('/update', '', 1)
    args = msg.split('\n', 2)

    if len(args) == 3:
        task_id, title, description = msg.split('\n', 2)
    else:
        task_id, title, description = args[0], args[1], ''

    timestamp = time.time()
    task_id = int(task_id)

    task = db.hget(f'/tasks/chat_id/{message.chat.id}', task_id)

    print(f'task = {task}')
    task = decode(task)
    task['title'] = title
    task['description'] = description
    task['modified'] = timestamp

    db.hset(f'/tasks/chat_id/{message.chat.id}', task_id, encode(task))
    return bot.reply_to(message, f'Modified task with id {task_id}')


@bot.message_handler(regexp=r"\d+")
def get_task_simple(message):
    try:
        task_id = int(message.text.replace('/', '', 1).strip().split()[0])
    except Exception:
        bot.reply_to(message, "Wrong syntax!")

    task = db.hget(f'/tasks/chat_id/{message.chat.id}', task_id)

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


@bot.message_handler(commands=['task'])
@validate(task_id=arg(int, required=True))
def get_task(message, task_id):
    task = db.hget(f'/tasks/chat_id/{message.chat.id}', task_id)

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


@bot.message_handler(commands=['export'])
def export(message):
    with TemporaryFile() as f:
        last_task_id = db.get(
            f'/tasks/chat_id/{message.chat.id}/last_task_id')

        if not last_task_id:
            return bot.reply_to(message, "There are no records.")

        task, *_ = db.hmget(f'/tasks/chat_id/{message.chat.id}', last_task_id)

        fieldnames = sorted(['task_id'] + list(decode(task).keys()))
        f.write((','.join(fieldnames)).encode())

        for t in db.hscan_iter(f'/tasks/chat_id/{message.chat.id}'):
            f.write(b'\n')
            task = decode(t[1])
            task['task_id'] = t[0].decode()
            row = ','.join([str(task[field]) for field in fieldnames])
            f.write(row.encode('utf-8'))

        f.seek(0)

        bot.send_document(message.chat.id, f, caption='report.csv')


@bot.message_handler(commands=['help'])
def help_msg(message):
    return bot.reply_to(message, HELP)


@bot.message_handler(commands=['start'])
def start(message):
    return bot.reply_to(message, 'Here will be start message')
