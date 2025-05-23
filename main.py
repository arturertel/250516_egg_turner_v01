
import uasyncio as asyncio
import pins
from lib.stepper import Stepper
from lib.mp_button import Button

from global_state import ping_pong_active, direction, speed, center_active


def ping_pong_switch(button, event):
    global ping_pong_active
    global center_active
    if event == Button.PRESSED:
        center_active = False  # Deaktivieren der Center-Funktion
        ping_pong_active = not ping_pong_active  # Umschalten der Funktion
        print("btn ping_pong")


btn_ping_pong = Button(pin=pins.btn_ping_pong_pin,
                       internal_pullup=True,
                       debounce_time=50,
                       callback=ping_pong_switch)


def center_switch(button, event):
    global ping_pong_active
    global center_active
    if event == Button.PRESSED:
        ping_pong_active = False  # Deaktivieren der Ping Pong-Funktion
        center_active = not center_active  # Umschalten der Funktion
        print("btn center")


btn_center = Button(pins.btn_center_pin,
                    internal_pullup=True,
                    debounce_time=50,
                    callback=center_switch)


def speed_switch(button, event):
    global speed
    if event == Button.PRESSED:
        if speed == 100:
            speed = 3000
            pins.led_speed.on()
        elif speed == 3000:
            speed = 100
            pins.led_speed.off()


btn_speed = Button(pins.btn_speed_pin,
                   internal_pullup=True,
                   debounce_time=50,
                   callback=speed_switch)
motor = Stepper(
    step_pin=pins.motor_step_pin,
    dir_pin=pins.motor_dir_pin,
    # Optional, wenn du den Motor aktivieren/deaktivieren möchtest
    en_pin=pins.motor_enable_pin,
    invert_enable=True,
    # Schritte pro Umdrehung (angepasst je nach deinem Motor)
    steps_per_rev=200 * 16,  # 200 Schritte pro Umdrehung * 16 Microsteps
    speed_sps=1000            # Schritte pro Sekunde (Geschwindigkeit)
)
# Bei 1/16 Microstepping müssen alle MS1, MS2, MS3 auf HIGH gesetzt werden.
pins.motor_ms1.on()
pins.motor_ms2.on()
pins.motor_ms3.on()


# State-Flags: wurden die Limit-Schalter wieder losgelassen?
limit_r_ready = True
limit_l_ready = True


def on_limit_r_event(button, event):
    global direction
    global limit_r_ready
    global limit_l_ready
    if event == Button.RELEASED and limit_r_ready:
        print("Limit rechts erreicht → Richtungswechsel")
        motor.stop()
        direction = -1
        limit_r_ready = False
        limit_l_ready = True
    elif event == Button.PRESSED:
        limit_r_ready = True
    return event


def on_limit_l_event(button, event):
    global direction
    global limit_r_ready
    global limit_l_ready
    if event == Button.RELEASED and limit_l_ready:
        print("Limit links erreicht → Richtungswechsel")
        motor.stop()
        direction = 1
        limit_l_ready = False
        limit_r_ready = True
    elif event == Button.PRESSED:
        limit_l_ready = True
    return event


limit_r = Button(pin=pins.limit_r_pin,
                 internal_pullup=True,
                 debounce_time=50,
                 callback=on_limit_r_event)

limit_l = Button(pin=pins.limit_l_pin,
                 internal_pullup=True,
                 debounce_time=50,
                 callback=on_limit_l_event)


async def buttons():
    while True:
        btn_ping_pong.update()
        limit_r.update()
        limit_l.update()

        btn_speed.update()
        btn_center.update()
        await asyncio.sleep_ms(10)  # oder 20–50 je nach Bedarf


async def motor_controller():
    global direction, speed, ping_pong_active
    global center_active
    pins.motor_reset_pin.value(1)
    pins.motor_sleep.value(1)

    def check_abort() -> bool:
        if not center_active:
            print("center aborted")
            motor.stop()
            motor.enable(False)
            pins.led_ping_pong.off()
            pins.led_center.off()
            return True
        return False

    while True:
        motor.speed(speed)

        if ping_pong_active and speed == 3000:
            print("Motor Ping Pong")
            motor.free_run(direction)
            motor.enable(True)
            pins.led_ping_pong.on()
            pins.led_center.off()

        elif ping_pong_active:
            print("Motor Ping Pong")
            motor.enable(True)
            pins.led_ping_pong.on()
            pins.led_center.off()

            steps_per_burst = 100
            pause_total = 39120   # 39120  Millisekunden = 
            pause_step = 100    # wie oft prüfen wir den Zustand (in ms)

            while ping_pong_active:
                for _ in range(steps_per_burst):
                    motor.enable(True)
                    motor.step(direction)
                    await asyncio.sleep_ms(2)
                    motor.enable(False)

                # 8 Sekunden Pause, aber unterbrechbar
                waited = 0
                while waited < pause_total:
                    if not ping_pong_active:
                        break
                    await asyncio.sleep_ms(pause_step)
                    waited += pause_step

        elif center_active:
            motor.speed(speed)
            print("Zentrierung gestartet")
            pins.led_ping_pong.off()
            pins.led_center.on()
            motor.enable(True)

            # Schritt 1: Nach links fahren
            motor.free_run(-1)
            while pins.limit_l_pin.value() == 0:
                if check_abort():
                    break
                await asyncio.sleep_ms(5)
            motor.stop()
            motor.overwrite_pos(0)
            await asyncio.sleep_ms(100)

            # Schritt 2: Nach rechts fahren
            motor.free_run(1)
            while pins.limit_r_pin.value() == 0:
                if check_abort():
                    break
                await asyncio.sleep_ms(5)
            motor.stop()
            steps_total = motor.get_pos()
            await asyncio.sleep_ms(100)

            # Schritt 3: Zur Mitte fahren
            center_pos = steps_total // 2
            motor.target(center_pos)
            motor.track_target()
            print(f"Fahre zur Mitte: {center_pos} Schritte")

            while not motor.is_target_reached():
                if check_abort():
                    break
                await asyncio.sleep_ms(10)

            print("Zentriert!")
            motor.stop()
            motor.enable(False)
            pins.led_center.off()
            center_active = False

        else:
            motor.stop()
            motor.enable(False)
            pins.led_ping_pong.off()
            pins.led_center.off()

        await asyncio.sleep_ms(50)


async def main():
    await asyncio.gather(
        buttons(),
        motor_controller()
    )


asyncio.run(main())
