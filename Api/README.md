# 项目名称

这是一个基于 FastAPI 的设备管理服务。该服务能够添加设备、检查设备是否已存在，并对设备进行布控。

### 前提条件
在开始之前，请确保您已在系统中安装了以下依赖项：

Python 3.10 或更高版本

pip（Python 包管理工具）

# 安装步骤

#### 克隆项目：
```
git clone <项目仓库链接>
cd <项目目录>
```


#### 创建虚拟环境（可选）：

建议在虚拟环境中安装 Python 依赖：

```
python3 -m venv venv
source venv/bin/activate
```

#### 安装依赖：
项目使用 httpx 作为 HTTP 客户端，FastAPI 作为 Web 框架，uvicorn 作为 ASGI 服务器。你可以通过以下命令安装这些依赖：
```
python3 -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

如果没有 requirements.txt 文件，你可以手动安装依赖：


```
pip install fastapi uvicorn httpx
```

### 如何运行服务

#### 启动 FastAPI 服务：

使用 uvicorn 启动该服务，默认端口为 9012：

`uvicorn API:app --host 0.0.0.0 --port 9012`

这里 API:app 表示 FastAPI 应用在 API.py 文件中定义的 app 对象。



激活虚拟环境

`source venv/bin/activate`

启动服务

`uvicorn main:app --host 0.0.0.0 --port 9012`

系统需求 操作系统：Linux (Ubuntu, CentOS, 等)
Python 版本：3.8 及以上
网络要求：确保能够访问远程 API 地址（如 192.168.10.232:9001 等）
