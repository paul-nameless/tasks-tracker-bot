import json
import uuid
from unittest.mock import MagicMock

import handlers
import pytest
from handlers import new, do, done, todo
from singleton import db
from telebot import types
from telebot.apihelper import ApiException
from utils import Status, decode


def setup_module(module):
    handlers.bot = MagicMock()


@pytest.fixture
def message(cmd):
    params = {'text': ''.join(cmd), }
    chat = types.User(uuid.uuid4().hex, False, 'test')
    from_user = types.User(uuid.uuid4().hex, False, 'testUser')
    return types.Message(
        uuid.uuid4().hex, from_user, None, chat, 'text', params, ""
    )


@pytest.mark.parametrize(
    'cmd', [
        ('/new ', 'task1', '\nDesctiption1'),
        ('/new ', 'Task1', '\nDesctiption1'),
        ('/new ', 'Task1', ''),
        ('/new ', 'Task1', '\n'),
    ]
)
def test_new(cmd, message):
    new(message)
    assert handlers.bot.reply_to.called
    key = db.get(f'/tasks/chat_id/{message.chat.id}/last_task_id')
    assert int(key) == 1
    task = decode(db.hget(f'/tasks/chat_id/{message.chat.id}', key))
    assert task['status'] == Status.TODO
    assert task['title'] == cmd[1].capitalize()


@pytest.mark.parametrize(
    'cmd, status', [
        (('/do ', '1'), Status.DO),
        (('/done ', '1'), Status.DONE),
        (('/todo ', '1'), Status.TODO),
    ]
)
def test_status(cmd, status, message):
    checking_changing_status(cmd, message, status)


@pytest.mark.parametrize(
    'cmd, status', [
        (('/do ', '1234'), Status.DO),
        (('/do ', '1a'), Status.DO),
        (('/do ', '-1a'), Status.DO),
        (('/do ', '-1'), Status.DO),
        (('/do ', 'das'), Status.DO),
        (('/done ', '1234'), Status.DONE),
        (('/done ', '1a'), Status.DONE),
        (('/done ', '-1a'), Status.DONE),
        (('/done ', '-1'), Status.DONE),
        (('/done ', 'das'), Status.DONE),
        (('/todo ', '1234'), Status.TODO),
        (('/todo ', '1a'), Status.TODO),
        (('/todo ', '-1a'), Status.TODO),
        (('/todo ', '-1'), Status.TODO),
        (('/todo ', 'das'), Status.TODO),
    ]
)
def test_status_no_such_id(cmd, status, message):
    try:
        checking_changing_status(cmd, message, Status.DO)
    except ApiException:
        pass


def checking_changing_status(cmd, message, status):
    """
    Before starting tests method create only one task with key 1.
    """

    key = db.incr(f'/tasks/chat_id/{message.chat.id}/last_task_id')

    task = {
        'title': 'TestTitle',
        'description': 'TeskDesc',
        'created': 0,
        'modified': 0,
        'status': Status.DO if status is Status.TODO else Status.TODO,
        'assignee': '',
        'assignee_id': '',
    }

    db.hset(f'/tasks/chat_id/{message.chat.id}',
            key, json.dumps(task).encode())

    if status is Status.DO:
        do(message)
    elif status is Status.TODO:
        todo(message)
    elif status is Status.DONE:
        done(message)
    else:
        assert status in Status.ALL

    assert handlers.bot.reply_to.called
    task = decode(db.hget(f'/tasks/chat_id/{message.chat.id}', key))
    assert task['status'] == status
