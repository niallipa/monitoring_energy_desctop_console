import requests
import datetime
import minimalmodbus
import time
import configparser
import os

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '..', 'setting.ini'))

TIME_SLEEP = config.getint('MainSetting', 'timeout')

URL_BASE = config.get('MainSetting', 'url_base')
# ИД Вышки
apgs_id = config.get('MainSetting', 'apgs_id')

device_status_id = config.get('MainSetting', 'device_status_id')
parameter_temp_id = config.get('MainSetting', 'parameter_temp_id')
parameter_h_id = config.get('MainSetting', 'parameter_h_id')
com_port = config.get('MainSetting', 'com_port')

measurement_temp_id = config.get('MainSetting', 'measurement_temp_id')
measurement_h_id = config.get('MainSetting', 'measurement_h_id')

register_temp_id = config.get('MainSetting', 'register_temp_id')
register_h_id = config.get('MainSetting', 'register_h_id')

def get_norms(apgs_id, device_apgs_id, parameter_id):
    url = f'{URL_BASE}/api/apgs/{apgs_id}/devices/{device_apgs_id}/parameters/{parameter_id}/norm'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Optional: Raise an exception if the request was not successful
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def get_device_status_id(measurement_value, norm):
    if measurement_value > norm['min_val_zel'] and measurement_value < norm['max_val_zhelt']:
        return 1
    elif measurement_value > norm['max_val_zel'] and measurement_value < norm['min_val_zhelt']:
        return 2
    else:
        return 3


def send_equipment_sensor_data(apgs_id, device_apgs_id, parameter_id, measurement_id, measurement_value):
    url = f'{URL_BASE}/api/apgs/{apgs_id}/devices/{device_apgs_id}'
    norm = get_norms(apgs_id, device_apgs_id, parameter_id)
    if not norm:
        return

    device_status_id = get_device_status_id(measurement_value, norm)
    data = {
        "parameter_id": parameter_id,
        "measurement_id": measurement_id,
        "device_status_id": device_status_id,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "norm_prm_device_apgs_id": norm['norm_prm_device_apgs_id'],
        "measurement_value": measurement_value,
    }

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()

        print('Data saved successfully')
    except Exception as err:
        print('Error occurred:', err)


def get_value(sensor_id):
    instrument = minimalmodbus.Instrument(com_port, 1, mode=minimalmodbus.MODE_RTU)
    instrument.serial.baudrate = 9600
    instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout = 1
    instrument.close_port_after_each_call = True
    datchik_data = instrument.read_registers(1, 2, functioncode=4)
    if sensor_id == register_temp_id:
        datchik_data[0] = datchik_data[0] / 100
        return datchik_data[0]
    if sensor_id == register_h_id:
        datchik_data[1] = datchik_data[1] / 100
        return datchik_data[1]
    print(datchik_data)


# send_equipment_sensor_data(apgs_id, device_status_id_v, 41)

while True:
    # первая температура, вторая влажность
    send_equipment_sensor_data(apgs_id, device_status_id, parameter_temp_id, measurement_temp_id, get_value(register_temp_id))
    send_equipment_sensor_data(apgs_id, device_status_id, parameter_h_id, measurement_h_id, get_value(register_h_id))
    time.sleep(TIME_SLEEP)