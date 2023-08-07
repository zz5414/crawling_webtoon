'''
웹툰을 다운받기에 앞서 특정 extension을 사용하기 위해
모니터별로 어느 위치에 있는지 먼저 확인한다
'''
from pynput.mouse import Listener

def on_click(x, y, button, pressed):
    if pressed:
        print('Mouse clicked at ({0}, {1})'.format(x, y))

# Using a listener to track mouse events
with Listener(on_click=on_click) as listener:
    listener.join()
