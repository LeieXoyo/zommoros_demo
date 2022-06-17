import sys
import traceback

from zommoros.utils.alert import sendmail

args = sys.argv

if len(args) == 1:
    from zommoros.config import prenv
    exec(prenv)
    from IPython import embed
    embed()
elif len(args) == 2:
    if args[1] != 'test' and input('即将开启实盘模式, 请确认(Yes): ') != 'Yes':
        sys.exit()
    exec(f'from zommoros.recipe.strategies.{args[1]}_strategy import run')
    try:
        run()
    except Exception as e:
        sendmail('Error', traceback.format_exc())
        raise(e)
else:
    raise('参数错误!')
