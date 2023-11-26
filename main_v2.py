import requests
import datetime
import minimalmodbus
import time
import json
import os

local_setting_path = os.path.join(os.path.dirname(__file__), 'setting.json')
global_setting_path = os.path.join(
    os.path.dirname(__file__), '..', 'setting.json')

with open(local_setting_path, encoding='utf-8') as f:
    setting = json.load(f)

# Основные параметры
DEFAULT = setting['DEFAULT']
TIME_SLEEP = DEFAULT['timeout']
URL_BASE = DEFAULT['url_base']
APGS_ID = DEFAULT['apgs_id']

DEVICES = setting['devices']


def get_norms(apgs_id, device_apgs_id, parameter_id):
    url = f'{URL_BASE}/api/apgs/{apgs_id}/devices/{device_apgs_id}/parameters/{parameter_id}/norm'
    try:
        response = requests.get(url)
        # Optional: Raise an exception if the request was not successful
        response.raise_for_status()
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

        print('Данные отправлены успешно')
    except Exception as err:
        print('Error occurred:', err)

def get_value(
    com_port, device_port, baundrate,
    register_address, num_registers, function_code,
    parameter_port
):
    instrument = minimalmodbus.Instrument(
        com_port, device_port, mode=minimalmodbus.MODE_RTU)
    instrument.serial.baudrate = baundrate
    instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout = 1
    instrument.close_port_after_each_call = True
    datchik_data = instrument.read_registers(
        register_address, num_registers, functioncode=function_code)
    return datchik_data[parameter_port] / 100


# send_equipment_sensor_data(apgs_id, device_status_id_v, 41)
# Переберает все настройки отправляет их в БД
def post_all_devices():
    for device in DEVICES:
        # Перебираем все девайсы
        device_id = device['device_id']
        com_port = device['com_port']
        device_port = device['device_port']
        baudrate = device['baudrate']
        register_address = device['register_address']
        num_registers = device['num_registers']
        function_code = device['function_code']
        parameters = device['parameters']
        print(f'Девайс: {device_id}')
        print(f'Порт: {com_port}, девайс: {device_port}, баудит: {baudrate}, регистр: {register_address}, нормеры: {num_registers}, функция: {function_code}')
        print('ПАРАМЕТРЫ:')
        for parameter in parameters:
            # Перебираем все параметры
            parameter_id = parameter['parameter_id']
            measurement_id = parameter['measurement_id']
            parameter_name = parameter['name']
            port = parameter['port']
            print(f'Параметр: {parameter_id}, измерение: {measurement_id}, название параметра: {parameter_name}, порт: {port}')
            # Получаем значения на устройстве
            try: 
                measurement_value = get_value(
                    com_port, device_port, baudrate,
                    register_address, num_registers, function_code,
                    port
                )
                print(f'Значение получено успешно')
            except Exception as err:
                print('Ошибка получения с порта: ', err)
                continue
            print(f'Значение: {measurement_value}')
            send_equipment_sensor_data(
                APGS_ID, device_id, parameter_id, measurement_id, measurement_value)
            
        print('====================')

while True:
    try:
        post_all_devices()
    except Exception as e:
        print("============= ОШИБКА ========================")
        print(e)
        print("============= END ОШИБКА ========================")
    time.sleep(TIME_SLEEP)
