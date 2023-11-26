import requests
import datetime
import minimalmodbus
import time
import json
import os

local_setting_path = os.path.join(os.path.dirname(__file__), 'setting.json')
global_setting_path = os.path.join(
    os.path.dirname(__file__), '..', 'setting.json')

with open(global_setting_path, encoding='utf-8') as f:
    setting = json.load(f)

# Основные параметры
DEFAULT = setting['DEFAULT']
TIME_SLEEP = DEFAULT['timeout']
URL_BASE = DEFAULT['url_base']
APGS_ID = DEFAULT['apgs_id']

PARAMETERS = setting['parameters']

def get_norms(apgs_id, device_apgs_id, parameter_id, equipment_id):
    url = f'{URL_BASE}/api/apgs/{apgs_id}/devices/{device_apgs_id}/parameters/{parameter_id}/equipments/{equipment_id}/norm'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data


def get_device_status_id(measurement_value, norm):
    if measurement_value >= norm['min_val_zel'] and measurement_value <= norm['max_val_zhelt']:
        return 1
    elif measurement_value >= norm['min_val_zhelt'] and measurement_value <= norm['max_val_zel']:
        return 2
    else:
        return 3


def send_equipment_sensor_data(apgs_id, device_apgs_id, equipment_id, parameter_id, measurement_id, measurement_value):
    url = f'{URL_BASE}/api/apgs/{apgs_id}/devices/{device_apgs_id}/equipments/{equipment_id}'
    norm = get_norms(apgs_id, device_apgs_id, parameter_id, equipment_id)
    
    device_status_id = get_device_status_id(measurement_value, norm)
    data = {
        "parameter_id": parameter_id,
        "measurement_id": measurement_id,
        "device_status_id": device_status_id,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "norm_prm_device_apgs_id": norm['norm_prm_device_apgs_id'],
        "measurement_value": measurement_value,
    }

    response = requests.post(url, json=data)
    response.raise_for_status()

def get_value(
    com_port, device_port, mode, 
    baundrate, parity, stopbits, timeout,
    register_address, num_registers, function_code,
    close_port_after_each_call, port, coeff
):
    instrument = minimalmodbus.Instrument(
        com_port, device_port, mode=mode)
    instrument.serial.baudrate = baundrate
    instrument.serial.parity = parity
    instrument.serial.stopbits = stopbits
    instrument.serial.timeout = timeout
    instrument.close_port_after_each_call = close_port_after_each_call
    datchik_data = instrument.read_registers(
        register_address, num_registers, functioncode=function_code)
    data_port = datchik_data[port]
    float_data = float(data_port)
    return round(float_data * coeff, 6)


# send_equipment_sensor_data(apgs_id, device_status_id_v, 41)
# Переберает все настройки отправляет их в БД
def post_all_devices():
        for parameter_id, parameter_config in PARAMETERS.items():
            server_config = parameter_config['server']
            client_config = parameter_config['client']

            print(f"Обработка параметра ID {parameter_id}:")

            # Вывод данных для сервера
            device_id = server_config['device']['device_id']
            equipment_id = server_config['equipment']['equipment_id']
            parameter_name = server_config['parameter']['name']
            measurement_name = server_config['parameter']['measurement_name']
            device_name = server_config['device']['device_name']
            print(f"  Для сервера: Устройство ID - {device_id}, Название устройства - {device_name}, Оборудование ID - {equipment_id}, Параметр - {parameter_name}, Единицы измерения - {measurement_name}")

            # Вывод данных для клиента
            com_port = client_config['instrument_base']['com_port']
            device_port = client_config['instrument_base']['device_port']
            mode =  client_config['instrument_base']['mode']
            print(f"  Для клиента: COM порт - {com_port}, Порт устройства - {device_port}, Режим - {mode}")

            # Получить параметры для отправки на сервер
            apgs_id = APGS_ID
            device_apgs_id = server_config['device']['device_id']
            equipment_id = server_config['equipment']['equipment_id']
            parameter_id = server_config['parameter']['parameter_id']
            measurement_id = server_config['parameter']['measurement_id']
            
            # Получение данных из клиентской конфигурации
            instrument_base = client_config['instrument_base']
            com_port = instrument_base['com_port']
            device_port = instrument_base['device_port']
            mode = instrument_base['mode']
            
            instrument_serial = client_config['instrument_serial']
            baudrate = instrument_serial['baudrate']
            parity = instrument_serial['parity']
            stopbits = instrument_serial['stopbits']
            timeout = instrument_serial['timeout']
            print(f'  Настройки: timeout - {timeout}, baudrate - {baudrate}, parity - {parity}, stopbits - {stopbits}')
            
            registers = client_config['registers']
            register_address = registers['register_address']
            num_registers = registers['num_registers']
            function_code = registers['function_code']
            print(f'  Настройки: register_address - {register_address}, num_registers - {num_registers}, function_code - {function_code}')

            other = client_config['other']
            close_port_after_each_call = other['close_port_after_each_call']
            port = other['port']
            coeff = other['coeff']

            # Получить параметры для отправки на сервер
            apgs_id = APGS_ID
            device_apgs_id = server_config['device']['device_id']
            equipment_id = server_config['equipment']['equipment_id']
            parameter_id = server_config['parameter']['parameter_id']
            measurement_id = server_config['parameter']['measurement_id']
            
            # Получить значение из устройства
            try:
                measurement_value = get_value(com_port, device_port, mode, baudrate, parity, stopbits, timeout, register_address, num_registers, function_code, close_port_after_each_call, port, coeff)
                print(f"  Значение с устройства: {measurement_value}")
            except Exception as e:
                print(f"  Ошибка при получении значения для параметра: {e}")
                continue

            # # Определить статус параметра
            # try:
            #     norm = get_norms(apgs_id, device_apgs_id, parameter_id, equipment_id)
            #     device_status_id = get_device_status_id(measurement_value, norm)
            #     print(f"  Статус параметра: ID статуса - {device_status_id}")
            # except Exception as e:
            #     print(f"  Ошибка при определении статуса параметра: {e}")
            #     continue

            # Отправить данные на сервер
            try:
                send_equipment_sensor_data(apgs_id, device_apgs_id, equipment_id, parameter_id, measurement_id, measurement_value)
                print("  Данные успешно отправлены на сервер")
            except Exception as e:
                print(f"  Ошибка при отправке данных на сервер: {e}")


while True:
    try:
        post_all_devices()
    except Exception as e:
        print("============= ОШИБКА ========================")
        print(e)
        print("============= END ОШИБКА ========================")
    time.sleep(TIME_SLEEP)