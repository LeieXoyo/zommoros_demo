from zommoros.recipe.kline_pattern import *

def fetch_kline_pattern(data):
    kp = []
    if top_brake(data):
        kp.append('top_brake')
    if bottom_brake(data):
        kp.append('bottom_brake')
    if top_hammer(data):
        kp.append('top_hammer')
    if bottom_hammer(data):
        kp.append('bottom_hammer')
    if top_split(data):
        kp.append('top_split')
    if bottom_split(data):
        kp.append('bottom_split')
    return kp
    