# 酒店房态管理系统

一个基于 FastAPI + Vue 3 的酒店房态管理系统，支持管理员登录、房间状态新增/更新、查询和删除。后端将房态数据优先写入 MySQL，数据库操作成功后同步更新 Redis 缓存；前端通过 Axios 调用后端接口并展示房态看板。

## 一、项目技术栈

| 部分 | 技术 |
| --- | --- |
| 后端 | Python、FastAPI、Uvicorn、Tortoise-ORM、MySQL、Redis、JWT |
| 前端 | Vue 3、TypeScript、Vite、Vue Router、Axios、Element Plus |
| 接口文档 | FastAPI 自动生成 Swagger 文档 |

## 二、导入库及作用

### 1. 后端 Python 标准库

| 库或模块 | 作用 |
| --- | --- |
| `typing.Any` | 为异常处理函数中的动态数据提供类型标注。 |
| `datetime` | 生成 JWT 的过期时间。`timezone` 用于处理带时区的时间。 |

### 2. 后端第三方库

| 库或模块 | 作用 |
| --- | --- |
| `fastapi` | 创建 Web API、定义路由、请求参数和 HTTP 异常。 |
| `fastapi.exceptions.RequestValidationError` | 捕获请求参数校验失败异常。 |
| `fastapi.encoders.jsonable_encoder` | 将异常详情转换为可以返回 JSON 的数据。 |
| `CORSMiddleware` | 配置跨域访问，允许 Vue 开发服务器调用后端。 |
| `JSONResponse` | 返回统一格式的 JSON 响应。 |
| `Jinja2Templates` | 渲染后端模板页面。 |
| `StaticFiles` | 挂载并提供静态文件，例如图片、CSS 或 JavaScript 文件。 |
| `pydantic.BaseModel` | 定义和校验接口请求体，例如房间信息和登录信息。 |
| `tortoise.contrib.fastapi.register_tortoise` | 将 Tortoise-ORM 注册到 FastAPI 应用生命周期中。 |
| `tortoise.fields` | 定义数据库字段类型，例如房间编号和房态。 |
| `tortoise.models.Model` | 定义数据库模型基类。 |
| `tortoise.exceptions.DBConnectionError` | 捕获数据库连接异常。 |
| `tortoise.exceptions.IntegrityError` | 捕获数据库完整性约束异常。 |
| `redis` | 连接 Redis，并读写房间状态缓存。 |
| `jwt`（PyJWT） | 生成管理员登录成功后的 JWT token。 |
| `uvicorn` | 启动 FastAPI 开发服务器。 |

### 3. 前端 npm 依赖

| 依赖 | 作用 |
| --- | --- |
| `vue` | 前端核心框架，用于编写登录页、房态看板等组件。 |
| `vue-router` | 管理前端路由，实现登录页与房态页面跳转及路由守卫。 |
| `axios` | 发送 HTTP 请求，调用 FastAPI 后端接口；请求拦截器会自动携带 JWT。 |
| `element-plus` | 提供按钮、表单、消息提示等 Vue 3 UI 组件。 |
| `vite` | 前端开发服务器和生产构建工具。 |
| `@vitejs/plugin-vue` | 让 Vite 支持编译 Vue 单文件组件。 |

## 三、项目目录

```text
酒店房态管理/
├─ 后端/
│  └─ hotel/
│     ├─ api/add_room.py       # 其他接口路由
│     ├─ main.py               # FastAPI 应用和主要接口
│     ├─ model.py              # Room 数据库模型
│     ├─ settings.py           # MySQL、JWT 等配置
│     ├─ template/home.html    # 后端模板页面
│     └─ static/                # 静态资源
├─ 前端/
│  └─ hotel/
│     ├─ src/Login.vue         # 管理员登录页
│     ├─ src/Hotel.vue         # 房态管理看板
│     ├─ src/api/http.ts       # Axios 实例和请求拦截器
│     ├─ src/router/index.ts   # 路由和登录守卫
│     ├─ src/App.vue           # 前端根组件
│     └─ package.json          # 前端依赖和启动脚本
└─ README.md
```

## 四、运行环境

启动前请确认以下服务已经安装并运行：

- Python 3.10 或更高版本
- Node.js 和 npm
- MySQL，数据库名为 `fastapi`
- Redis，默认地址为 `127.0.0.1:6379`

### 启动后端

进入后端目录，安装依赖后启动服务：

```powershell
cd "D:\酒店房态管理\后端\hotel"
pip install fastapi uvicorn tortoise-orm aiomysql redis PyJWT jinja2
python main.py
```

后端地址：`http://127.0.0.1:8001`

Swagger 接口文档：`http://127.0.0.1:8001/docs`

### 启动前端

```powershell
cd "D:\酒店房态管理\前端\hotel"
npm install
npm run dev
```

前端地址通常为：`http://127.0.0.1:5173`

## 五、默认登录信息

当前开发环境配置在 `后端/hotel/settings.py`：

```text
用户名：admin
密码：123456
```

正式部署时请修改管理员账号、密码和 `JWT_SECRET_KEY`，并建议改为环境变量配置，不要将真实密码提交到代码仓库。

## 六、主要接口

| 请求方式 | 地址 | 作用 |
| --- | --- | --- |
| `POST` | `/admin/login` | 管理员登录并获取 JWT token。 |
| `POST` | `/admin/register` | 注册管理员账号，密码以哈希形式保存。 |
| `POST` | `/room/set` | 新增或更新房间状态，先写 MySQL，再更新 Redis。 |
| `GET` | `/room/{room_id}` | 查询指定房间状态。 |
| `GET` | `/room` | 查询全部房间状态。 |
| `DELETE` | `/room/{room_id}` | 删除 MySQL 房间记录及 Redis 缓存。 |

登录后，前端将 token 保存在 `localStorage`，Axios 请求拦截器会自动添加以下请求头：

```http
Authorization: Bearer <token>
```

## 七、数据同步逻辑

房间新增或更新时，系统按照以下顺序处理：

1. 将房间状态写入 MySQL。
2. MySQL 操作成功后，更新 Redis 中的 `room:{room_id}` 缓存。
3. 如果 Redis 更新失败，接口会返回错误，但 MySQL 中已经成功保存的数据不会回滚。

## 八、http异常表速查
状态码	含义	使用场景
400	Bad Request 请求错误	请求参数语义错误、业务校验失败（如房间状态非法）
401	Unauthorized 未认证	管理员登录失败、Token 缺失 / Token 过期 / 用户名密码错误，需要登录
403	Forbidden 权限不足	登录成功，但没有操作权限（普通账号不能删除房间）
404	Not Found 资源不存在	查询房间 ID 不存在、接口地址写错
422	Validation Error 参数校验失败	Pydantic 模型校验失败，类型错误、缺少必填字段（RequestValidationError）
500	Internal Server Error 服务器内部错误	数据库异常、代码报错、Redis 连接失败等服务端问题

