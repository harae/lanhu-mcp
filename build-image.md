# 构建命令
docker build -t lanhu-mcp:multiuser .

# 运行

## 运行前先确保宿主机目录存在
mkdir -p data logs db

## 运行命令，端口 9800，并把 data、logs、db 都挂到宿主机
docker run -d \
  --name lanhu-mcp-multiuser \
  --restart unless-stopped \
  --env-file .env \
  -e SERVER_HOST=0.0.0.0 \
  -e SERVER_PORT=9800 \
  -p 9800:9800 \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/db:/app/db" \
  lanhu-mcp:multiuser

# 启动后访问：
配置页：http://localhost:9800/account-config
MCP 地址：http://localhost:9800/mcp?account=你的账号&role=Developer&name=你的名字

# 本地进程常驻
mkdir -p data logs db && SERVER_HOST=0.0.0.0 SERVER_PORT=9800 nohup python3 lanhu_mcp_server.py > logs/lanhu-mcp.out 2>&1 &

# 查看进程
ps aux | grep 'python3 lanhu_mcp_server.py'