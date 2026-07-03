#!/bin/bash
# 六爻神数 — 预测模式入口
# usage: bash scripts/oracle_predict.sh <主队> <客队> [--v8]

if [ $# -lt 2 ]; then
    echo "用法: bash scripts/oracle_predict.sh <主队英文名> <客队英文名>"
    echo "示例: bash scripts/oracle_predict.sh Argentina Cape Verde"
    exit 1
fi

cd /c/Users/huang
python six_lines_oracle_v8.py "$1" "$2" 2>&1
