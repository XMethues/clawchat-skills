#!/usr/bin/env bash
# ============================================================
# Tarot Liveware — 首次安装设置
# ============================================================
# 用法: bash liveware/scripts/setup.sh
#
# 功能:
#   1. liveware 登录
#   2. 创建 app
#   3. 注册到 ClawChat
#   4. 启动服务器 + 绑定隧道
# ============================================================
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LIVEWARE_DIR="$SKILL_ROOT/liveware"
PORT="${1:-5080}"
APP_NAME="tarot"

echo "🃏 Tarot Liveware — 首次安装"
echo ""

# ── 1. Login ──────────────────────────────────────────────
echo "🔑 liveware 登录..."
# 尝试从 HERMES_HOME/.env 读取 CLAWCHAT_TOKEN
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
ENV_FILE="${HERMES_HOME}/.env"

if [ -f "$ENV_FILE" ]; then
  set -a
  source "$ENV_FILE" 2>/dev/null || true
  set +a
fi

if [ -n "${CLAWCHAT_TOKEN:-}" ]; then
  liveware login --access-token "$CLAWCHAT_TOKEN" 2>&1 | tail -1
  echo "   ✅ 已登录"
else
  echo "   ⚠️ 未找到 CLAWCHAT_TOKEN，跳过登录"
  echo "   可手动执行: liveware login --access-token \"\$CLAWCHAT_TOKEN\""
fi
echo ""

# ── 2. Create app ─────────────────────────────────────────
echo "📦 创建 app..."
APP_OUTPUT=$(liveware app create "$APP_NAME" --agent-type hermes 2>&1 || true)
APP_ID=$(echo "$APP_OUTPUT" | grep -oP 'appId\s+\K(app-\S+)' || echo "")
if [ -z "$APP_ID" ]; then
  # 可能已经存在，尝试获取
  APP_ID=$(liveware app list 2>/dev/null | grep "$APP_NAME" | awk '{print $2}' || echo "")
fi

if [ -z "$APP_ID" ]; then
  echo "   ❌ 无法获取 app ID"
  exit 1
fi
echo "   ✅ App ID: $APP_ID"
echo ""

# ── 3. Save app ID for later use ──────────────────────────
APP_ID_FILE="${HOME}/.clawling/tarot-app-id"
mkdir -p "$(dirname "$APP_ID_FILE")"
echo "$APP_ID" > "$APP_ID_FILE"
echo "   ✅ App ID 已保存到 $APP_ID_FILE"
echo ""

# ── 4. Register to ClawChat ──────────────────────────────
echo "🔗 注册到 ClawChat..."
APP_URL="https://${APP_ID}.apps.clawling.io"
# 这里需要 Hermes 的 clawchat_register_app 工具来注册，
# 如果是在 Hermes 会话中运行，用下面的命令提示
echo "   请在 Hermes 中执行:"
echo "   clawchat_register_app(appId=\"$APP_ID\", name=\"Tarot Arcana\", url=\"$APP_URL\")"
echo ""

# ── 4. Start server + bind tunnel ────────────────────────
echo "🚀 启动本地服务器 (port $PORT)..."
cd "$LIVEWARE_DIR"
nohup python3 server.py --port "$PORT" > /tmp/tarot-server.log 2>&1 &
SERVER_PID=$!
echo "   PID: $SERVER_PID (日志: /tmp/tarot-server.log)"

# 等待服务器就绪
for i in $(seq 1 10); do
  if curl -s -o /dev/null -w "" "http://127.0.0.1:$PORT/" 2>/dev/null; then
    echo "   ✅ 服务器就绪"
    break
  fi
  sleep 1
done

echo ""
echo "🔗 绑定隧道..."
liveware tunnel bind "$APP_ID" "http://127.0.0.1:$PORT"
echo ""

echo "═══════════════════════════════════════════"
echo "✅ Tarot Liveware 已激活!"
echo "   公网: $APP_URL"
echo "   本地: http://127.0.0.1:$PORT"
echo "═══════════════════════════════════════════"
