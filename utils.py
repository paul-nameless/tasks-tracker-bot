import json
import logging
import logging.handlers
import time

from singleton import bot, db

logger = logging.getLogger(__name__)


class Status:
    TODO = 'TODO'
    DO = 'DO'  # in progress
    DONE = 'DONE'
    ALL = (TODO, DO, DONE)


def init_log():
    handlers = [logging.StreamHandler()]

    # capture warnings, along with asyncio runtime warnings
    # e.g. RuntimeWaring: coroutine <X> was never awaited
    logging.captureWarnings(True)

    logging.basicConfig(
        format='%(levelname)-8s [%(asctime)s] %(message).1000s',
        level=logging.DEBUG,
        handlers=handlers,
    )


def encode(msg):
    return json.dumps(msg).encode()


def decode(msg):
    return json.loads(msg.decode())


def change_status_task(message, task_id, status):

    assert status in Status.ALL

    task = db.hget(f'/tasks/chat_id/{message.chat.id}', task_id)
    if task is None:
        bot.reply_to(message, 'No task with such id')
        return None

    task = decode(task)
    task['status'] = status
    task['modified'] = time.time()
    task['assignee_id'] = message.from_user.id
    task['assignee'] = f'@{message.from_user.username}'

    db.hset(f'/tasks/chat_id/{message.chat.id}', task_id, encode(task))
    return task
