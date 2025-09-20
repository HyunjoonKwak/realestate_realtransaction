#!/bin/bash

# Real Estate Manager 시작 스크립트

APP_NAME="realestate_manager"
PID_FILE="app.pid"
LOG_FILE="app.log"

echo "📍 Real Estate Manager 시작 중..."

# 이미 실행 중인지 확인
if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  애플리케이션이 이미 실행 중입니다 (PID: $PID)"
        echo "   중지하려면 ./stop.sh 를 실행하세요"
        exit 1
    else
        echo "🧹 오래된 PID 파일 정리 중..."
        rm -f $PID_FILE
    fi
fi

# 백그라운드에서 애플리케이션 실행
echo "🚀 백그라운드에서 애플리케이션 시작..."
nohup python main.py > $LOG_FILE 2>&1 &
APP_PID=$!

# PID 저장
echo $APP_PID > $PID_FILE

echo "✅ 애플리케이션이 백그라운드에서 시작되었습니다"
echo "   PID: $APP_PID"
echo "   로그 파일: $LOG_FILE"
echo "   웹 접속: http://localhost:8080"
echo ""
echo "📝 명령어:"
echo "   로그 확인: tail -f $LOG_FILE"
echo "   애플리케이션 중지: ./stop.sh"