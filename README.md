# Tasks tracker bot for telegram

[![Build Status](https://travis-ci.org/paul-nameless/tasks-tracker-bot.svg?branch=master)](https://travis-ci.org/paul-nameless/tasks-tracker-bot)

Telegram bot to track tasks in small teams

## Test

```
docker run -d -p 127.0.0.1:6379:6379 --name redis redis:4.0.11-alpine
pip install -r requirements.txt
export API_TOKEN=[TELEGRAM_API_TOKEN]
python main.py
```


## How to run tests

```
bash run-tests.sh
```


## Commands

new - create new task
do - mark task's status as DO
done - mark task's status as DONE
todo - mark task's status as TODO
tasks - output all tasks
update - update task title and description
export - export all tasks
help - show help message
start - start using bot
