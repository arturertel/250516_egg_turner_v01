from machine import Pin

# buttons
btn_speed_pin = Pin(10, Pin.IN, Pin.PULL_UP)
btn_center_pin = Pin(11, Pin.IN, Pin.PULL_UP)
btn_ping_pong_pin = Pin(12, Pin.IN, Pin.PULL_UP)

# limit switches
limit_r_pin = Pin(14, Pin.IN, Pin.PULL_UP)  # IN = Abfragen OUT = Ansteuern
limit_l_pin = Pin(15, Pin.IN, Pin.PULL_UP)  # PULL_UP = 3.3 V, PULL_DOWN = 0 V

# LEDS
led_speed = Pin(2, Pin.OUT)
led_center = Pin(3, Pin.OUT)
led_ping_pong = Pin(4, Pin.OUT)

# motor
motor_reset_pin = Pin(19, Pin.OUT)
motor_enable_pin = Pin(18, Pin.OUT)  # 0 = disable, 1 = enable
motor_dir_pin = Pin(16, Pin.OUT)  # 0 = left, 1 = right
motor_step_pin = Pin(17, Pin.OUT)  # 0 = low, 1 = high
motor_ms1 = Pin(8, Pin.OUT)
motor_ms2 = Pin(7, Pin.OUT)
motor_ms3 = Pin(6, Pin.OUT)
motor_sleep = Pin(5, Pin.OUT)
