import uuid
from unittest.mock import MagicMock

import handlers
import pytest
from handlers import new
from singleton import db
from telebot import types
from utils import Status, decode


def setup_module(module):
    handlers.bot = MagicMock()


@pytest.fixture
def message(cmd):
    params = {'text': ''.join(cmd)}
    chat = types.User(uuid.uuid4().hex, False, 'test')
    return types.Message(
        uuid.uuid4().hex, None, None, chat, 'text', params, ""
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
