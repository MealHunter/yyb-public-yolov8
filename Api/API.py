from fastapi import FastAPI, Form
import httpx
import asyncio  # 用于延迟
import uuid
import random

app = FastAPI()

# 用于存储已经添加过的设备及其对应的 code
history = {}
host = "192.168.10.231"


def gen_random_code_s(prefix):
    """
    产生随机编号（服务于数据表的的编号）
    :param prefix: 编码前缀
    :return:
    """
    val = str(uuid.uuid5(uuid.uuid1(), str(uuid.uuid1())))
    a = val.split("-")[0]
    code = "%s%s%d" % (prefix,a, random.randint(10000, 99999))

    return code

@app.post("/videolAnalysisSystem/")
async def submit_device_name(deviceCode: str = Form(...)):
    login_url = f"http://{host}:9001/login"
    target_url = f"http://{host}:9001/stream/add"

    login_data = {
        "username": "admin",
        "password": "admin888"
    }

    async with httpx.AsyncClient() as client:
        # 1. 登录获取 Session
        login_response = await client.post(login_url, data=login_data)
        if login_response.status_code != 200:
            return {"error": "Login failed", "status": login_response.status_code}

        # 2. 登录成功后，带着 Session 访问需要的页面
        # 2. 检查 deviceCode 是否已经存在于 history 字典中

        # 运行已经存在的设备
        if deviceCode in history:
            code = history[deviceCode]  # 如果已存在，直接获取对应的 code
            # await asyncio.sleep(15)
            print(f"设备 {deviceCode} 已存在，关联的 code 为 {code}")
            # 设备存在后直接选择转发
            while True:
                form_data = {
                    'code': code,
                    'handle': 'add'
                }
                response = await client.post(f"http://{host}:9001/stream/postHandleForward", data=form_data,
                                                 follow_redirects=True)
                if response.status_code == 200:
                    print("请求成功")
                    break  # 请求成功后跳出循环

                await asyncio.sleep(2)  # 延迟1秒再发请求

            # 如果转发成功，点击开启布控
            await asyncio.sleep(4)
            if response.status_code == 200:
                form_data = {
                    'controlCode': code
                }
                response = await client.post(f"http://{host}:9001/api/postAddAnalyzer", data=form_data, follow_redirects=True)

            return {
                "status": response.status_code,
                "content": response.text[:500],
                "code": code
            }
        # 运行需要添加的设备
        else:
            # 生成随机 code
            code = gen_random_code_s(prefix="cam")
            print(code)
            # 表单
            form_data = {
                'handle': 'add',
                'code': code,
                'app': 'live',
                'name': code,
                'rtspUrl': f'rtsp://{host}:9554/live/{code}',
                'httpMp4Url': f'http://{host}:9002/live/{code}.live.mp4',
                'hlsUrl': f'http://{host}:9002/live/{code}.hls.m3u8',
                'pull_stream_url': f'rtsp://show.hhdlink.online:554/live/{deviceCode}', # rtsp://show.hhdlink.online:554/live/{deviceCode}
                'nickname': deviceCode,
                'remark': '123'
            }
            # 3. 添加设备
            # await asyncio.sleep(5)
            response = await client.post(target_url, data=form_data, follow_redirects=True)
            if response.status_code == 200:
                # 如果添加成功，将 deviceCode 和 code 存储到 history 字典中
                history[deviceCode] = code
                print(f"设备 {deviceCode} 添加成功，关联的 code 为 {code}")
            else:
                return {"error": "Failed to add device", "status": response.status_code}

            # 如果添加成功，延迟2秒后点击开启转发按钮
            # await asyncio.sleep(15)  # 延迟2秒
            while True:
                if response.status_code == 200:
                    form_data = {
                        'code': code,
                        'handle': 'add'
                    }
                    response = await client.post(f"http://{host}:9001/stream/postHandleForward", data=form_data, follow_redirects=True)
                    if response.status_code == 200:
                        print("请求成功")
                        break  # 请求成功后跳出循环

                    await asyncio.sleep(2)  # 延迟1秒再发请求

            await asyncio.sleep(4)  # 延迟2秒
            # 如果开启转发成功，添加布控信息
            if response.status_code == 200:
                control_form_data = {
                    'controlCode': code,
                    'algorithmCode': 'onnxruntime_yolo8',  # 算法代码（根据实际情况修改）
                    'objectCode': 'person,bicycle,car,motorcycle,airplane,bus,train,truck,boat,traffic light,fire hydrant,stop sign,parking meter,bench,bird,cat,dog,horse,sheep,cow,elephant,bear,zebra,giraffe,backpack,umbrella,handbag,tie,suitcase,frisbee,skis,snowboard,sports ball,kite,baseball bat,baseball glove,skateboard,surfboard,tennis racket,bottle,wine glass,cup,fork,knife,spoon,bowl,banana,apple,sandwich,orange,broccoli,carrot,hot dog,pizza,donut,cake,chair,couch,potted plant,bed,dining table,toilet,tv,laptop,mouse,remote,keyboard,cell phone,microwave,oven,toaster,sink,refrigerator,book,clock,vase,scissors,teddy bear,hair drier,toothbrush',  # 目标对象代码（例如：'person'）
                    'polygon': '0.0000,0.0000,1.0000,0.0000,1.0000,1.0000,0.0000,1.0000',  # 如果有指定的多边形区域，填入对应的坐标数据
                    'pushStream': '1',  # 开启推流，使用 '1' 表示 True
                    'minInterval': '180',  # 最小间隔时间，单位为秒
                    'classThresh': '0.5',  # 分类阈值
                    'overlapThresh': '0.5',  # 重叠阈值
                    'remark': 'This is a remark',  # 备注信息
                    # Stream 信息
                    'streamApp': 'live',  # 流应用名称
                    'streamName': code,  # 流名称
                    'streamVideo': 'h264/12/1920x1080',  # 视频流信息
                    'streamAudio': '无'  # 音频流信息（如果有音频，填写对应音频信息）
                }
                control_response = await client.post(f"http://{host}:9001/api/postAddControl", data=control_form_data, follow_redirects=True)
                print("Control data sent:", control_form_data)
                print("Control response:", control_response.text)

                # 如果布控成功，延迟2秒后点击开启布控
                if response.status_code == 200:
                    form_data = {
                        'controlCode': code
                    }
                    response = await client.post(f"http://{host}:9001/api/postAddAnalyzer", data=form_data, follow_redirects=True)

            return {
                "status": response.status_code,
                "content": response.text[:500],
                "code": code
            }


# @app.post("/delete-device/")
# async def delete_device(code: str = Form(...)):
#     login_url = "http://127.0.0.1:9001/login"
#
#     login_data = {
#         "username": "admin",
#         "password": "admin888"
#     }
#
#     async with httpx.AsyncClient() as client:
#         # 1. 登录获取 Session
#         login_response = await client.post(login_url, data=login_data)
#         if login_response.status_code != 200:
#             return {"error": "Login failed", "status": login_response.status_code}
#
#         # 2.删除布控
#         form_data = {
#             'controlCode': code
#         }
#         response = await client.post("http://127.0.0.1:9001/api/postDelControl", data=form_data, follow_redirects=True)
#
#         # 3.删除原视频流
#         if response.status_code == 200:
#             form_data = {
#                 'code': code
#             }
#             response = await client.post("http://127.0.0.1:9001/stream/postDel", data=form_data, follow_redirects=True)
#
#         return {
#             "status": response.status_code,
#             "content": response.text[:500]
#         }
#
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9012)
