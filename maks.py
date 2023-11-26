import minimalmodbus

instrument = minimalmodbus.Instrument('COM5', 1, mode=minimalmodbus.MODE_RTU)
instrument.serial.baudrate = 115200
instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout = 1
instrument.close_port_after_each_call = True
datchik_data = instrument.read_registers(0x3100, 20, functioncode=4)
datchik_data[0]=datchik_data[0]/100
#напряжение ФЭМ
datchik_data[1]=datchik_data[1]/100
#сила тока ФЭМ
datchik_data[9]=datchik_data[9]/100
#потребляемая мощность(ВТ)(лампочка)
datchik_data[10]=datchik_data[10]/100
#потребляемая сила тока (А)(лампочка)
datchik_data[3]=datchik_data[3]/100
#сила тока потребителя
datchik_data[4]=datchik_data[4]/100
#напряжение АКБ
datchik_data[5]=datchik_data[5]/100
#заряд АКБ
print(datchik_data)