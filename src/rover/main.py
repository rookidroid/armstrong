import socket
import network
from machine import Pin, PWM
import utime

ssid = 'tank'
password = 'tank1234'

ap = network.WLAN(network.AP_IF)
ap.config(essid=ssid, password=password)
ap.active(True)


while ap.active() == False:
    pass

print('Connection successful')
print(ap.ifconfig())

led = Pin("LED", machine.Pin.OUT)

MID = 1500000
MIN = 1000000
MAX = 2000000

left_pwm = PWM(Pin(0))
left_pwm.freq(50)
left_pwm.duty_ns(MID)

right_pwm = PWM(Pin(1))
right_pwm.freq(50)
right_pwm.duty_ns(MID)

center_var_x = 1850
center_var_y = 1790
scale_x_upper = (MAX-MID)/(4096-center_var_x)
scale_x_lower = (MAX-MID)/(center_var_x)
scale_y_upper = (MAX-MID)/(4096-center_var_y)
scale_y_lower = (MAX-MID)/(center_var_y)

udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.settimeout(2)

try:
    udp_socket.bind(('', 1234))
except OSError as err:
    print(err)
else:
    while True:
        try:
            data, addr = udp_socket.recvfrom(4096)

            if data:
                led.on()
                data_str = data.decode()
                print(data_str)
                data_list = data_str.split(':')
                main_dutycycle = MID
                offset_dutycycle = 0
                for idx, cmd in enumerate(data_list):
                    if cmd:
                        
                        if cmd[0] == 'Y':
                            #print(int(cmd[1:]))
                            if int(cmd[1:]) >= center_var_y:
                                main_dutycycle = (center_var_y - int(cmd[1:]))*scale_y_upper
                            else:
                                main_dutycycle = (center_var_y - int(cmd[1:]))*scale_y_lower
                            
                            #time_ns = int(cmd[1:])
                            #if time_ns >= MIN and time_ns <= MAX:
                            #    left_pwm.duty_ns(int(cmd[1:]))
                            #else:
                            #    left_pwm.duty_ns(MID)
                        elif cmd[0] == 'X':
                            if int(cmd[1:]) >= center_var_x:
                                offset_dutycycle = (center_var_x - int(cmd[1:]))*scale_x_upper
                            else:
                                offset_dutycycle = (center_var_x - int(cmd[1:]))*scale_x_lower
                            #print(int(cmd[1:]))
                            #time_ns = int(cmd[1:])
                            #if time_ns >= MIN and time_ns <= MAX:
                            #    right_pwm.duty_ns(int(cmd[1:]))
                            #else:
                            #    right_pwm.duty_ns(MID)
                
                left_duty = round(-(main_dutycycle+offset_dutycycle)+MID)
                right_duty = round(-(main_dutycycle-offset_dutycycle)+MID)
                print(left_duty)
                print(right_duty)
                if left_duty >= MIN and left_duty <= MAX:
                    left_pwm.duty_ns(left_duty)
                elif left_duty < MIN:
                    left_pwm.duty_ns(MIN)
                elif left_duty > MAX:
                    left_pwm.duty_ns(MAX)
                
                if right_duty >= MIN and right_duty <= MAX:
                    right_pwm.duty_ns(right_duty)
                elif right_duty < MIN:
                    right_pwm.duty_ns(MIN)
                elif right_duty > MAX:
                    right_pwm.duty_ns(MAX)

                led.off()
            #led.toggle()
        except OSError:
            print('no data')
            left_pwm.duty_ns(MID)
            right_pwm.duty_ns(MID)