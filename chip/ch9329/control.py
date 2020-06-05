# Core code of HID.
# Build commands for HID keyboard and mouse.

import time
import math
import random
from lib import screen
from chip.ch9329 import map

screen_resolution = screen.get_zoom_resolution()
screen_ratio = screen.get_zoom_ratio()

hid_com = None

hid_command_keys = [
    "LEFT_CTRL",
    "RIGHT_CTRL",
    "LEFT_SHIFT"
    "RIGHT_SHIFT",
    "LEFT_ALT",
    "RIGHT_ALT",
    "LEFT_WIN",
    "RIGHT_WIN"
]


def set_com(which_com):
    global hid_com
    hid_com = which_com


# [累加和]收尾
# 关于SUM累加和的理解：SUM = HEAD+ADDR+CMD+LEN+DATA
# 如鼠标释放: 57 AB 00 02 08 00 00 00 00 00 00 00 00 0C
# SUM=57+AB+2+8=10C，然后只取低位十六进制数0C
def get_tail_low(put):
    tail_sum = 0x00
    for i in put:
        tail_sum += i
    _, tail_low = divmod(tail_sum, 0x100)
    return tail_low


# 获取鼠标xyz轴的偏移值
def get_xyz(val):
    if val == 0:
        return 0
    val = math.floor(val)
    offset = val
    if val > 0:
        if val > 127:
            offset = 127
    elif val < 0:
        if val < -127:
            val = -127
        offset = 256 - abs(val)
    return offset


# 释放键盘
def keyboard_free():
    global hid_com
    if hid_com is None:
        return
    hid_com.write(bytes([0x57, 0xAB, 0x00, 0x02, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0C]))
    time.sleep(0.075)


# keys 只支持Command键 + 6个普通按键组合
# delay 毫秒，释放延时
def keyboard(keys, delay):
    global hid_com
    if hid_com is None:
        return
    target_keys = {
        "command": None,
        "normal": []
    }
    keys_type = type(keys)
    if keys_type == str:
        keys = str.upper(keys)
        if keys in hid_command_keys:
            target_keys["command"] = map.keyboard[keys]
        else:
            target_keys["normal"].append(map.keyboard[keys])
    elif keys_type == int:
        keys = str.upper(str(keys))
        if keys in hid_command_keys:
            target_keys["command"] = map.keyboard[keys]
        else:
            target_keys["normal"].append(map.keyboard[keys])
    elif keys_type == list or keys_type == tuple:
        for v in keys:
            if type(v) == int:
                v = str(v)
            v = str.upper(v)
            if v in hid_command_keys:
                target_keys["command"] = map.keyboard[v]
            else:
                target_keys["normal"].append(map.keyboard[v])

    # 固有头部
    put = [0x57, 0xAB, 0x00, 0x02, 0x08]
    # 命令键组合判断
    if target_keys["command"] is not None:
        put.append(target_keys["command"])
    else:
        put.append(0x00)
    # 这一位必须是 0x00
    put.append(0x00)
    # 最多 6 个组合键
    for i in range(0, 6):
        try:
            put.append(target_keys["normal"][i])
        except TypeError:
            put.append(0x00)
        except IndexError:
            put.append(0x00)
    # [累加和]收尾
    put.append(get_tail_low(put))
    # 按下组合键
    hid_com.write(bytes(put))
    if delay > 0:
        time.sleep(0.001 * delay)
    keyboard_free()


# keyboard 的拓展,支持一个句子
def word(words, delay):
    for k in words:
        keyboard(k, delay)


# 当前鼠标按键
mouse_cur_btn = "NONE"


# 鼠标立刻移动到({"x": 0, "y": 0})
def mouse_portal(position):
    global hid_com
    x = position["x"]
    y = position["y"]
    if x is None or y is None or x < 0 or y < 0:
        return
    if hid_com is None:
        return
    if x > screen_resolution[0] - 50:
        x = screen_resolution[0] - 50
    if y > screen_resolution[1] - 50:
        y = screen_resolution[1] - 50
    put = [0x57, 0xAB, 0x00, 0x04, 0x07, 0x02, 0x00]
    if x is None:
        put.append(0x00)  # x坐标低位
        put.append(0x00)  # x坐标高位
    else:
        x_high, x_low = divmod(math.floor(x * 4096 / screen_resolution[0]), 0x100)
        put.append(x_low)
        put.append(x_high)
    if y is None:
        put.append(0)  # y坐标低位
        put.append(0)  # y坐标高位
    else:
        y_high, y_low = divmod(math.floor(y * 4096 / screen_resolution[1]), 0x100)
        put.append(y_low)
        put.append(y_high)
    put.append(0x00)
    # [累加和]收尾
    put.append(get_tail_low(put))
    # 操作鼠标
    hid_com.write(bytes(put))
    time.sleep(0.1)


# 鼠标移动到({"x": 0, "y": 0})
# x偏移像素
# 向右为 1->127，向左为 -1->-127
# 向右为 0x01->0x7F，向左为 0x80->0xFF
def mouse_move(position):
    global mouse_cur_btn
    global hid_com
    x = position["x"]
    y = position["y"]
    if x is None or y is None or x < 0 or y < 0:
        return
    if hid_com is None:
        return

    if x > screen_resolution[0] - 50:
        x = screen_resolution[0] - 50
    if y > screen_resolution[1] - 50:
        y = screen_resolution[1] - 50

    # 获取当前鼠标的位置
    sx, sy = screen.get_mouse_position()

    step = math.floor(screen_ratio * random.randint(5, 6))
    abs_x = abs(x - sx)
    abs_y = abs(y - sy)

    if abs_x < 3:
        px = 0
    elif abs_x < step:
        px = x - sx
    else:
        px = step if x > sx else -step

    if abs_y < 3:
        py = 0
    elif abs_y < step:
        py = y - sy
    elif px == 0:
        py = step if y > sy else -step
    else:
        py = math.floor(abs(px) / abs_x * (y - sy))

    while True:
        ex, ey = screen.get_mouse_position()
        # px
        if px > 0 and ex >= x:
            px = 0
        elif px < 0 and ex <= x:
            px = 0
        # py
        if py > 0 and ey >= y:
            py = 0
        elif py < 0 and ey <= y:
            py = 0
        if px == 0 and py == 0:
            mouse_portal(position)
            break
        put = [
            0x57, 0xAB, 0x00, 0x05, 0x05, 0x01,
            map.mouse[mouse_cur_btn],
            get_xyz(px + random.randint(-1, 1)),
            get_xyz(py + random.randint(-1, 1)),
            0x00
        ]
        # [累加和]收尾
        put.append(get_tail_low(put))
        # 操作鼠标
        hid_com.write(bytes(put))
        time.sleep(0.01)


# 鼠标中键滚轮滚动
def mouse_roll(z):
    global hid_com
    if z is None:
        return
    if hid_com is None:
        return
    # [固定头部 0 - 5 ,按键 6, 0 0 0]
    put = [0x57, 0xAB, 0x00, 0x05, 0x05, 0x01, 0x00, 0x00, 0x00, get_xyz(z), 0x00]
    # [累加和]收尾
    put.append(get_tail_low(put))
    # 操作鼠标
    hid_com.write(bytes(put))
    time.sleep(0.1)


# 按下鼠标（不释放）
# button LEFT | RIGHT | MID
def mouse_press(button):
    global mouse_cur_btn
    global hid_com
    if button is None:
        return
    if hid_com is None:
        return
    mouse_cur_btn = button
    # [固定头部 0 - 5 ,按键 6, 0 0 0]
    put = [0x57, 0xAB, 0x00, 0x05, 0x05, 0x01, map.mouse[button], 0x00, 0x00, 0x00]
    # [累加和]收尾
    put.append(get_tail_low(put))
    # 操作鼠标
    hid_com.write(bytes(put))
    time.sleep(0.1)


# 释放鼠标按压
def mouse_free():
    global mouse_cur_btn
    global hid_com
    mouse_cur_btn = "NONE"
    if hid_com is None:
        return
    hid_com.write(bytes([0x57, 0xAB, 0x00, 0x05, 0x05, 0x01, 0x00, 0x00, 0x00, 0x00, 0x0D]))
    time.sleep(0.1)
