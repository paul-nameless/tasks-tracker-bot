import logging

import utils
from handlers import bot

log = logging.getLogger(__name__)


def main():
    utils.init_log()
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()
