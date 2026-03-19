#!/bin/bash
# 小精靈啟動器 for macOS
# 雙擊此檔案即可自動安裝並啟動遊戲

cd "$(dirname "$0")"

echo "=========================================="
echo "  小精靈 Pac-Man 啟動器"
echo "=========================================="

if ! command -v python3 &>/dev/null; then
    echo ""
    echo "❌ 找不到 Python3"
    echo "請先安裝 Python3：https://www.python.org/downloads/"
    echo ""
    read -p "按 Enter 離開..."
    exit 1
fi

PY=$(command -v python3)
echo "✅ Python: $($PY --version)"

echo "🔧 檢查並安裝依賴套件（首次需要網路，之後不用）..."
$PY -m pip install --quiet --upgrade pygame numpy 2>/dev/null || \
pip3 install --quiet --upgrade pygame numpy 2>/dev/null

echo "✅ 依賴套件就緒"
echo ""
echo "🎮 啟動遊戲..."
echo "  方向鍵移動  │  ESC 離開  │  R 重玩"
echo ""

$PY 遊戲主程式.py

echo ""
echo "遊戲已結束。"
