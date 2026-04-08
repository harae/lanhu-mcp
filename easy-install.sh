#!/bin/bash

# 蓝湖 MCP Server - 超级简单安装脚本
# 专为小白用户设计，交互式引导安装

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 清屏
clear

echo -e "${BOLD}${BLUE}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║                                                   ║"
echo "║     🎨 蓝湖 MCP Server - 一键安装程序            ║"
echo "║                                                   ║"
echo "║     让 AI 助手共享团队知识，打破 AI IDE 孤岛     ║"
echo "║                                                   ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${GREEN}欢迎！这个脚本会帮你自动完成所有安装步骤${NC}"
echo -e "${GREEN}预计耗时：3-5 分钟${NC}"
echo ""
echo -e "按 ${BOLD}Enter${NC} 开始安装，或按 ${BOLD}Ctrl+C${NC} 取消"
read

# ============================================
# 步骤 1: 环境检查
# ============================================

echo ""
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}📦 步骤 1/5: 检查系统环境${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查 Python
echo -e "正在检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未检测到 Python 3${NC}"
    echo ""
    echo "请先安装 Python 3.10 或更高版本："
    echo "  Mac: brew install python3"
    echo "  Ubuntu: sudo apt install python3 python3-pip"
    echo "  官网: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✅ Python $PYTHON_VERSION${NC}"

# 检查 pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ 未检测到 pip3${NC}"
    exit 1
fi
echo -e "${GREEN}✅ pip3 已安装${NC}"

# 检查 Git
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}⚠️  未检测到 Git（可选）${NC}"
else
    echo -e "${GREEN}✅ Git 已安装${NC}"
fi

echo ""
echo -e "${GREEN}🎉 环境检查通过！${NC}"
sleep 1

# ============================================
# 步骤 2: 安装依赖
# ============================================

echo ""
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}📥 步骤 2/5: 安装依赖包${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "正在创建 Python 虚拟环境..."
    python3 -m venv venv
    echo -e "${GREEN}✅ 虚拟环境创建完成${NC}"
else
    echo -e "${GREEN}✅ 虚拟环境已存在${NC}"
fi

# 激活虚拟环境
echo "正在激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "正在升级 pip..."
pip install --upgrade pip -q

# 安装依赖
echo "正在安装项目依赖..."
echo -e "${YELLOW}（这可能需要 1-2 分钟，请耐心等待）${NC}"
pip install -r requirements.txt -q

echo -e "${GREEN}✅ 依赖安装完成${NC}"

# 安装 Playwright 浏览器
echo ""
echo "正在安装 Playwright 浏览器..."
echo -e "${YELLOW}（首次安装需要下载 Chromium，可能需要 1-2 分钟）${NC}"
playwright install chromium

echo ""
echo -e "${GREEN}🎉 依赖安装完成！${NC}"
sleep 1

# ============================================
# 步骤 3: 配置蓝湖 Cookie
# ============================================

echo ""
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}🍪 步骤 3/5: 配置说明（Cookie 在网页里填，无需改 .env）${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 复制 .env.example 到 .env（端口等可选配置；LANHU_COOKIE 可不填，交给网页配置）
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ 已创建 .env 配置文件（可选：按需改端口等，不必改 Cookie）${NC}"
    else
        echo -e "${RED}❌ 未找到 .env.example 文件${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env 文件已存在${NC}"
fi

echo ""
echo -e "${BOLD}${GREEN}Cookie 在浏览器里配置即可${NC}，不需要打开 .env 粘贴 Cookie。"
echo ""
echo -e "  • 服务启动后，在本机浏览器打开：${BOLD}http://localhost:<端口>/account-config${NC}"
echo -e "  • 在页面填写「账号名」和从蓝湖复制的 Cookie，保存后写入 ${BOLD}db/account_cookies.json${NC}"
echo -e "  • Cursor 里 MCP 的 URL 要带 ${BOLD}account=与网页里相同的账号名${NC}"
echo ""
echo -e "${YELLOW}可选（高级）${NC}：若 MCP 地址 ${BOLD}不带${NC} ${BOLD}account${NC}，才会用 .env 里的 ${BOLD}LANHU_COOKIE${NC}；多数情况只用网页配置即可。"
echo ""
echo -e "${BOLD}请先在蓝湖复制 Cookie（下一步启动服务后，粘贴到配置页）：${NC}"
echo ""
echo -e "  1️⃣  在浏览器打开：${BOLD}${BLUE}https://lanhuapp.com${NC} 并登录"
echo ""
echo -e "  2️⃣  按下键盘 ${BOLD}F12${NC} 键（Mac 用户按 ${BOLD}Command+Option+I${NC}）"
echo "     会打开开发者工具"
echo ""
echo -e "  3️⃣  点击顶部的 ${BOLD}\"Network\"${NC}（网络）标签"
echo ""
echo -e "  4️⃣  按 ${BOLD}F5${NC} 刷新页面"
echo ""
echo -e "  5️⃣  在左侧请求列表中点击 ${BOLD}第一个请求${NC}"
echo ""
echo -e "  6️⃣  右侧找到 ${BOLD}\"Request Headers\"${NC} 部分"
echo "     找到 \"Cookie:\" 开头的那一行"
echo ""
echo -e "  7️⃣  ${BOLD}选中并复制${NC} 整个 Cookie 值"
echo "     （Cookie 很长，确保全部复制；可先留在剪贴板，启动服务后再粘贴到配置页）"
echo ""
echo -e "${BOLD}${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 若系统支持，仅打开蓝湖（不再打开 .env）
if command -v open &> /dev/null; then
    echo -e "需要帮你打开蓝湖网站吗？(y/n) [${BOLD}y${NC}]: "
    read -r open_lanhu
    open_lanhu=${open_lanhu:-y}
    if [ "$open_lanhu" = "y" ] || [ "$open_lanhu" = "Y" ]; then
        open "https://lanhuapp.com" 2>/dev/null || true
        echo -e "${GREEN}✅ 已打开浏览器${NC}"
        echo ""
    fi
fi

echo -e "${BOLD}准备好后按 Enter 继续（Cookie 可在启动服务后到配置页再填）${NC}"
read

echo ""
echo -e "下面用于生成 Cursor 配置示例：MCP URL 里的 ${BOLD}account=${NC} 必须与你稍后在 ${BOLD}账号配置页${NC} 填写的「账号名」一致。"
echo -e "请输入该账号标识 [${BOLD}default${NC}]: "
read -r MCP_ACCOUNT
MCP_ACCOUNT=${MCP_ACCOUNT:-default}
if [[ ! "$MCP_ACCOUNT" =~ ^[a-zA-Z0-9_.-]+$ ]]; then
    echo -e "${YELLOW}⚠️  仅允许字母、数字、. _ -，已改为 default${NC}"
    MCP_ACCOUNT=default
fi

echo ""
echo -e "${GREEN}✅ 示例将使用账号标识：${BOLD}${MCP_ACCOUNT}${NC}${GREEN}（请配置页填写同名）${NC}"
sleep 1

# ============================================
# 步骤 4: 创建数据目录
# ============================================

echo ""
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}📁 步骤 4/5: 创建数据目录${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 创建数据目录
mkdir -p data logs db
echo -e "${GREEN}✅ 数据目录已创建${NC}"

sleep 1

# ============================================
# 步骤 5: 启动服务
# ============================================

echo ""
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}🚀 步骤 5/5: 启动服务${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${GREEN}是否现在启动服务？(y/n) [${BOLD}y${NC}]: ${NC}"
read -r start_now
start_now=${start_now:-y}

# 与 lanhu_mcp_server.py 默认端口一致；若 .env 中配置了 SERVER_PORT 则优先
SERVER_PORT=8100
if [ -f ".env" ]; then
    _sp_line=$(grep -E '^SERVER_PORT=' .env | head -1 || true)
    if [ -n "$_sp_line" ]; then
        _sp_val="${_sp_line#SERVER_PORT=}"
        _sp_val="${_sp_val//\"/}"
        _sp_val="${_sp_val//\'/}"
        _sp_val="${_sp_val// /}"
        [ -n "$_sp_val" ] && SERVER_PORT="$_sp_val"
    fi
fi

if [ "$start_now" = "y" ] || [ "$start_now" = "Y" ]; then
    echo ""
    echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${GREEN}🎉 安装成功！服务正在启动...${NC}"
    echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}① 账号配置页（先打开，粘贴 Cookie 并保存）：${NC}"
    echo -e "   ${BOLD}http://localhost:${SERVER_PORT}/account-config${NC}"
    echo ""
    echo -e "${BOLD}② MCP 地址：${NC}http://localhost:${SERVER_PORT}/mcp"
    echo ""
    echo -e "${BOLD}下一步：在 Cursor 中配置 MCP${NC}"
    echo ""
    echo "请将以下配置添加到 Cursor 的 MCP 配置文件中（account 须与配置页里的账号名一致）："
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    cat << MCP_CONFIG
{
  "mcpServers": {
    "lanhu": {
      "url": "http://localhost:${SERVER_PORT}/mcp?account=${MCP_ACCOUNT}&role=Developer&name=YourName"
    }
  }
}
MCP_CONFIG
    echo -e "${YELLOW}提示：须先在配置页保存 Cookie；account 与网页里填的账号名一致即可（单人常用 default）${NC}"
    echo -e "${YELLOW}提示：部分 AI 开发工具不支持 URL 中文参数，建议使用英文${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}配置方法：${NC}"
    echo "  1. 打开 Cursor"
    echo "  2. 按 Command+Shift+P (Mac) 或 Ctrl+Shift+P (Windows)"
    echo "  3. 输入 'MCP' 找到 MCP 配置"
    echo "  4. 粘贴上面的配置"
    echo ""
    echo -e "按 ${BOLD}Ctrl+C${NC} 可以停止服务器"
    echo ""
    echo -e "${GREEN}正在启动服务器… 启动后请先打开上面的「账号配置页」完成 Cookie 配置。${NC}"
    echo ""
    
    # 运行服务器
    python lanhu_mcp_server.py
else
    echo ""
    echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${GREEN}🎉 安装成功！${NC}"
    echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "稍后运行服务器，请执行："
    echo -e "  ${BOLD}source venv/bin/activate${NC}"
    echo -e "  ${BOLD}python lanhu_mcp_server.py${NC}"
    echo ""
    echo -e "${BOLD}启动后请先打开：${NC}http://localhost:${SERVER_PORT}/account-config （填写 Cookie）"
    echo -e "${BOLD}MCP 地址示例：${NC}http://localhost:${SERVER_PORT}/mcp?account=${MCP_ACCOUNT}&role=Developer&name=YourName"
    echo ""
fi

