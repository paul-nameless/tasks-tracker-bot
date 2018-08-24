from utils import Status, bot


def validate(**kwargs):
    """Add comments here"""
    def wrapper(fun):
        def wrap(message, **_):
            args = message.text.split(' ')
            if len(args) > 1:
                del args[0]
            else:
                args = []

            res_kwargs = {}
            for i, k in enumerate(kwargs.keys()):
                validator, default, required = kwargs[k]
                if i < len(args):
                    value = args[i]
                else:
                    if required:
                        return bot.reply_to(
                            message,
                            f'Required field "{k}" of {validator.__name__} '
                            'type'
                        )
                    value = default

                try:
                    res_kwargs[k] = validator(value)
                except ValueError as e:
                    return bot.reply_to(
                        message,
                        f'Invalid type for "{k}" field: {str(e)} '
                    )

            return fun(message, **res_kwargs)
        return wrap
    return wrapper


def arg(_type, default=None, required=False):
    return _type, default, required


def status_enum(v):
    if v is None:
        return None
    v = v.upper()
    if v in Status.ALL or v == 'ALL':
        return v
    raise ValueError(
        f'Invalid enum type, expected one of: "{Status.ALL}" or "all"'
    )
