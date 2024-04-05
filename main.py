#!/usr/bin/env python3
# -*- coding: utf8 -*-
'''
Author       : Pooneyy
Date         : 2024-03-10 16:52:07
LastEditors  : Pooneyy 85266337+pooneyy@users.noreply.github.com
LastEditTime : 2024-04-02 19:53:02
FilePath     : /suanleme-copilot/main.py
Description  : “算了么”平台 suanleme-copilot

Copyright (c) 2024 by Pooneyy, All Rights Reserved. 
'''

import json
import datetime, pytz, time
import random
import requests

VERSION = 1.0
CONFIG = {}
HOST = "https://api.suanleme.cn/api/v1"
REFRESH_TOKEN = ''
TASK_IDS = []
NETWORK_STATUS_WARN_SWITCH = 0
'''网络状态警告开关。当且仅当值为`1`时，发送通知。设计成这样是确保不重复发送通知。'''
NETWORK_ERROR_RETRY_INTERVAL = 1800 # 网络错误检查间隔，单位：秒

def timeStamp_To_dateTime(timeStamp):return datetime.datetime.fromtimestamp(int(timeStamp), pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
def timeStamp_To_date(timeStamp):return datetime.datetime.fromtimestamp(int(timeStamp), pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d')
def isoDateTime_To_dateTime(iso_date_time):return datetime.datetime.strptime(iso_date_time, "%Y-%m-%dT%H:%M:%S.%f%z").strftime('%Y-%m-%d %H:%M:%S')
def isoDateTime_To_date(iso_date_time):return datetime.datetime.strptime(iso_date_time, "%Y-%m-%dT%H:%M:%S.%f%z").strftime('%Y-%m-%d')
def date_To_timeStamp(date):return int(time.mktime(time.strptime(date, "%Y-%m-%d")))
def get_last_month(timeStamp):return datetime.datetime.fromtimestamp(int((timeStamp - datetime.datetime.fromtimestamp(int(timeStamp), pytz.timezone('Asia/Shanghai')).day * 86400)), pytz.timezone('Asia/Shanghai')).strftime('%Y-%m')
def timeStamp_To_date_and_hour(timeStamp):
    '''获取时间戳对应的小时，例：`2024-03-10T16:`'''
    return datetime.datetime.fromtimestamp(int(timeStamp), pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%dT%H:')
def get_seconds_to_next_minute():
    '''计算当前时间距离下一整点的秒数'''
    return 60 - datetime.datetime.now().second
def get_seconds_to_next_hour():
    '''计算当前时间距离下一整点的秒数'''
    return 3600 - datetime.datetime.now().second - datetime.datetime.now().minute * 60
def get_current_dateTime():return timeStamp_To_dateTime(time.time())

def saveConfig():
    CONFIG['refresh_token'] = REFRESH_TOKEN
    with open("config.json", "w", encoding='utf8') as file:
        json.dump(CONFIG, file, ensure_ascii=False, indent = 4)

def loadConfig():
    global CONFIG, REFRESH_TOKEN
    with open("config.json", "r+", encoding='utf8') as file:
        CONFIG = json.load(file)
    REFRESH_TOKEN = CONFIG['refresh_token']

def checkNetwork():
    try:
        requests.get('https://www.baidu.com', timeout=5)
        return True
    except:return False

def init():
    global CONFIG, REFRESH_TOKEN
    print('初始化配置文件')
    account = input('请输入算了么账号：')
    password = input('请输入算了么密码：')
    CONFIG['refresh_token'] = ''
    CONFIG['pushplus_token'] = input('请输入pushplus推送加的token：')
    CONFIG['machines_remark'] = {
        "左边填写设备名称": "右边填写备注",
        "以下一个示例":"记得删去这几行",
        "LAPTOP-FHQA9KQL": "machine-0"
    }
    try:
        login(account, password)
        saveConfig()
        print('初始化完成，请重新运行')
    except:init()

def sendMsg(msg):
    data = {}
    url = "http://www.pushplus.plus/send"
    data['token'] = CONFIG['pushplus_token']
    data['title'] = '算了么任务状态'
    data['template'] = 'markdown'
    # data['topic'] = CONFIG['pushplus_topic'] # 群组编码，发送群组消息。
    data['content'] = msg
    response = requests.post(url,data=data)
    return response.text

def login(account, password):
    global REFRESH_TOKEN
    url = f"{HOST}/user/token"
    payload={
        'account': account,
        'password': password,
    }
    response = requests.post(url, data=payload)
    try:
        REFRESH_TOKEN = json.loads(response.text)['refresh']
        print(f"{get_current_dateTime()}\t登录成功")
    except KeyError:
        print(json.loads(response.text)['detail'])
        raise Exception('LoginError')

def get_user_info() -> dict:
    ''' 获取用户信息，其实是用这个函数检查算了么服务是否可用'''
    global REFRESH_TOKEN
    url = f"{HOST}/user/info"
    headers = {'Authorization': f'Bearer {refresh()}'}
    response = requests.get(url, headers=headers)
    try:json.loads(response.text)
    except:raise requests.exceptions.ConnectionError
    # return json.loads(response.text)

def refresh():
    global REFRESH_TOKEN
    url = f"{HOST}/user/token/refresh"
    payload={'refresh': REFRESH_TOKEN}
    response = requests.post(url, data=payload)
    REFRESH_TOKEN = json.loads(response.text)['refresh']
    return json.loads(response.text)["access"]

def get_current_hour_score_record():
    '''获取到当前小时的积分明细'''
    page = 1
    nextpage = 'next'
    results = []
    while nextpage:
        url = f"{HOST}/user/score_record/list?page={page}&score_type="
        headers = {'Authorization': f'Bearer {refresh()}'}
        response = requests.get(url, headers=headers)
        resp_results = json.loads(response.text)['results']
        for result in resp_results:
            if timeStamp_To_date_and_hour(time.time()) in result['created_time']:
                if result['type'] in ["MountingFee", "ReceivingOrders"]:
                    results.append(result)
        nextpage = json.loads(response.text)['next']
        page += 1
        if timeStamp_To_date_and_hour(time.time()-3600) in response.text:break
    return results

def get_ongoing_tasks_info()-> list:
    '''获取进行中的任务信息'''
    global REFRESH_TOKEN
    url = f"{HOST}/tasks/progress/"
    headers = {'Authorization': f'Bearer {refresh()}'}
    response = requests.get(url, headers=headers)
    return json.loads(response.text)

def get_machines_info()-> list:
    '''获取设备信息
    
    返回的数据结构：
    ```json
    [
        {
            "id": "49aedd68-30b0-4f71-81f4-44ec49854343",
            "auth_secret": "c01390a5-dc1f-413f-b9dc-6cf1b7633ec6",
            "version": "1.1.6",
            "name": "WIN-PZVIADNNBJU",
            "note": "{\"cpuModel\": \"Intel(R) Xeon(R)...}",
            "user_remark": "Y6 - 107 - 5154",
            "join_time": "2024-03-23T09:10:24.416862+08:00",
            "last_online": "2024-03-23T09:10:24.416876+08:00",
            "user": 29,
            "tags": [
                3,
                6
            ]
        }
    ]
    ```
    '''
    page = 1
    nextpage = 'next'
    records = []
    while nextpage:
        url = f"{HOST}/machines/?page={page}"
        headers = {'Authorization': f'Bearer {refresh()}'}
        response = requests.get(url, headers=headers)
        records.extend(json.loads(response.text)['results'])
        nextpage = json.loads(response.text)['next']
        page += 1
    return records

def get_a_machine_info(machine_id: str)-> dict:
    '''获取设备信息'''
    global REFRESH_TOKEN
    url = f"{HOST}/machines/{machine_id}/"
    headers = {'Authorization': f'Bearer {refresh()}'}
    response = requests.get(url, headers=headers)
    return json.loads(response.text)

def remark(deployment_task_ids:list, lost_deployment_task_ids:list, tasks_info:list):
    '''传入进行中的任务信息，比对现有的备注，如果备注与正在进行的任务不一致，则更新备注
    param deployment_task_ids             : list 进行中的任务id列表
    param lost_deployment_task_ids        : list 丢失的任务id列表
    param task_ids                        : list 进行中的任务信息
    '''
    tasks_info_dict = {i['id']:i for i in tasks_info}
    machines_info = get_machines_info()
    # 如果设备没有备注，而配置文件中已登记设备名，则将备注设为配置文件中的备注
    for machine in machines_info:
        if machine['user_remark']:...
        else:
            machine_name = machine['name']
            machine_remark = CONFIG['machines_remark'].get(machine_name)
            if machine_remark:
                remark = f"{machine_remark}"
                remark_result = set_machine_remark(machine['id'], remark)
                print(f"{get_current_dateTime()}\t{machine_name} 更新备注: {remark},{remark_result}")

    # 同步一下信息
    machines_info = get_machines_info()
    machines_info_dict = {i['id']:i for i in machines_info}

    # 处理正在进行的任务，比对运行它的机器的备注是否为正在进行的任务，如果不是，则更新备注
    for task in deployment_task_ids:
        machine_id = tasks_info_dict[task]['machine']
        machine_name = machines_info_dict[machine_id]['name']
        original_remark = machines_info_dict[machine_id]['user_remark']
        if original_remark: # 如果原始的备注不为空
            if str(task) in original_remark:continue # 且备注中包含任务id，则跳过
        # 否则
        machine_remark = CONFIG['machines_remark'].get(machine_name)
        if machine_remark: # 如果配置文件中已登记设备名
            remark = f"{machine_remark} - {tasks_info_dict[task]['task']} - {task}"
            remark_result = set_machine_remark(machine_id, remark)
            print(f"{get_current_dateTime()}\t{machine_name} 更新备注: {remark},{remark_result}")

    # 同步一下信息
    machines_info = get_machines_info()

    # 处理丢失的任务，如果设备列表中有失去任务的机器，则将设备的备注设为原始的备注
    for task in lost_deployment_task_ids:    # 遍历丢失的任务id
        for machine in machines_info:        # 遍历设备列表
            machine_id = machine['id']
            original_remark = machine['user_remark'] # 获取设备的原始备注
            if original_remark:              # 如果原始的备注不为空
                if str(task) in original_remark:    # 且备注中包含任务id
                    machine_name = machine['name']
                    machine_remark = CONFIG['machines_remark'].get(machine_name)
                    if machine_remark:         # 且配置文件中已登记设备名
                        remark = f"{machine_remark}"
                        remark_result = set_machine_remark(machine_id, remark)
                        print(f"{get_current_dateTime()}\t{machine_name} 更新备注: {remark},{remark_result}")

def set_machine_remark(machine_id: str, remark: str):
    '''设置设备备注'''
    global REFRESH_TOKEN
    url = f"{HOST}/machines/{machine_id}/edit_user_remark/"
    headers = {'Authorization': f'Bearer {refresh()}'}
    payload = {"user_remark": remark}
    response = requests.post(url, headers=headers, json=payload)
    return response.text

def main():
    global TASK_IDS, NETWORK_STATUS_WARN_SWITCH
    try:
        while True:
            loadConfig()
            get_user_info()
            score_record = get_current_hour_score_record()
            tasks_info = get_ongoing_tasks_info()
            # 将 tasks_info 中所有 task_type 为 Deployment 的任务的id组成一个列表
            deployment_task_ids = [task['id'] for task in tasks_info if task['task_type'] == 'Deployment']
            
            # 已结算的任务ID
            # 遍历当前这一小时内的积分明细，当 task['correlation_id'] 出现在 deployment_task_ids 中，
            # 则该id是“已经结算的长期任务id”，将其加入到列表 settled_task_ids 里。
            settled_task_ids = [task['correlation_id'] for task in score_record if task['correlation_id'] in deployment_task_ids]

            # 新增任务ID
            # 对比 deployment_task_ids 与 TASK_IDS ，查看 deployment_task_ids 增加了哪些id
            newly_added_deployment_task_ids = list(set(deployment_task_ids) - set(TASK_IDS))
            
            # 丢失的任务ID
            # 对比 deployment_task_ids 与 TASK_IDS ，查看 deployment_task_ids 减少了哪些id
            lost_deployment_task_ids = list(set(TASK_IDS) - set(deployment_task_ids))
            
            # 更新 TASK_IDS
            TASK_IDS = deployment_task_ids
            
            # deployment_task_ids中的id如果 settled_task_ids 中未出现，且在 newly_added_deployment_task_ids 中未出现
            # 进行中的任务id如果不在 已结算的id列表 内，【且】不在 新接取id列表 内，则将其加入 未结算的id列表 内。
            unsettled_task_ids = [task_id for task_id in deployment_task_ids if task_id not in settled_task_ids and task_id not in newly_added_deployment_task_ids]
            
            # 设置机器备注
            remark(deployment_task_ids, lost_deployment_task_ids, tasks_info)
            
            machines_info = get_machines_info()
            
            # 未结算的任务对应的 machine_id 与 machine_remark
            unsettled_tasks_info = {}
            for task_id in unsettled_task_ids:
                for task in tasks_info:
                    if task['id'] == task_id:
                        machine_id = task['machine']
                        break
                for machine in machines_info:
                    if machine['id'] == machine_id:
                        machine_remark = machine['user_remark']
                        break
                unsettled_tasks_info[task_id] = {'machine_id': machine_id, 'machine_remark': machine_remark}

            # 新增的 Deployment 任务对应的 machine_id 与 machine_remark
            newly_added_deployment_tasks_info = {}
            for task_id in newly_added_deployment_task_ids:
                for task in tasks_info:
                    if task['id'] == task_id:
                        machine_id = task['machine']
                        break
                for machine in machines_info:
                    if machine['id'] == machine_id:
                        machine_remark = machine['user_remark']
                        break
                newly_added_deployment_tasks_info[task_id] = {'machine_id': machine_id, 'machine_remark': machine_remark}

            msg = ''
            if NETWORK_STATUS_WARN_SWITCH >= 1:
                msg += f"{get_current_dateTime()}\t算了么服务网络已恢复\n"
            if newly_added_deployment_task_ids:
                print(f"{get_current_dateTime()}\t新增的任务 {', '.join(list(map(str, newly_added_deployment_task_ids)))}")
                msg += f"### 新增的任务\n|任务ID|机器备注|\n| ---- | ---- |\n"
                for i in newly_added_deployment_tasks_info:
                    msg += f"|{i}|{newly_added_deployment_tasks_info[i]['machine_remark']}|\n"
            if lost_deployment_task_ids:
                print(f"{get_current_dateTime()}\t丢失的任务 {', '.join(list(map(str, lost_deployment_task_ids)))}")
                msg += f"### 丢失的任务\n{', '.join(list(map(str, lost_deployment_task_ids)))}\n"
            if unsettled_tasks_info:
                msg += f"### 未正常结算的任务\n|任务ID|机器备注|\n| ---- | ---- |\n"
                print(f"{get_current_dateTime()}\t未结算的任务")
                for i in unsettled_tasks_info:
                    msg += f"|{i}|{unsettled_tasks_info[i]['machine_remark']}|\n"
                    print(f"\t\t\t{i}\t{unsettled_tasks_info[i]['machine_id']}\t{unsettled_tasks_info[i]['machine_remark']}")
            else:print(f"{get_current_dateTime()}\t无异常任务\r", end="")
            NETWORK_STATUS_WARN_SWITCH = 0
            if msg:sendMsg(msg)
            saveConfig()
            time.sleep(get_seconds_to_next_hour() + 60 + random.randint(0, 240))
    except KeyboardInterrupt:print("\n结束")
    except requests.exceptions.ConnectionError:
        NETWORK_STATUS_WARN_SWITCH += 1
        if checkNetwork():
            msg = "算了么服务网络异常"
            if NETWORK_STATUS_WARN_SWITCH == 1:sendMsg(msg)
            print(f"{get_current_dateTime()}\t{msg}\r", end="")
        else:print(f"{get_current_dateTime()}\t网络连接中断\r", end="")
        time.sleep(NETWORK_ERROR_RETRY_INTERVAL)
        main()
    except json.decoder.JSONDecodeError:
        NETWORK_STATUS_WARN_SWITCH += 1
        msg = "算了么服务异常"
        if NETWORK_STATUS_WARN_SWITCH == 1:sendMsg(msg)
        print(f"{get_current_dateTime()}\t{msg}\r", end="")
        time.sleep(NETWORK_ERROR_RETRY_INTERVAL)
        main()
    except requests.exceptions.ChunkedEncodingError:
        NETWORK_STATUS_WARN_SWITCH += 1
        msg = "远程主机关闭连接"
        if NETWORK_STATUS_WARN_SWITCH == 1:sendMsg(msg)
        print(f"{get_current_dateTime()}\t{msg}\r", end="")
        time.sleep(NETWORK_ERROR_RETRY_INTERVAL)
        main()

def index():
    global TASK_IDS
    try:
        loadConfig()
        get_user_info()
        tasks_info = get_ongoing_tasks_info()
        TASK_IDS = [task['id'] for task in tasks_info if task['task_type'] == 'Deployment']
        main()
    except requests.exceptions.ConnectionError:
        try:
            if checkNetwork():print(f"{get_current_dateTime()}\t目标主机网络异常\r", end="")
            else:print(f"{get_current_dateTime()}\t网络连接中断\r", end="")
            time.sleep(NETWORK_ERROR_RETRY_INTERVAL)
            index()
        except KeyboardInterrupt:print("结束")
    except requests.exceptions.ChunkedEncodingError:
        print(f"{get_current_dateTime()}\t远程主机关闭连接\r", end="")
        time.sleep(NETWORK_ERROR_RETRY_INTERVAL)
        index()
    except FileNotFoundError:
        try:init()
        except KeyboardInterrupt:print("\n退出，取消初始化")
    except KeyboardInterrupt:print("退出")

if __name__ == '__main__':
    index()
