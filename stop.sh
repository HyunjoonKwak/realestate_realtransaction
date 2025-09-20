#!/bin/bash

# Real Estate Manager 중지 스크립트

APP_NAME="realestate_manager"
PID_FILE="app.pid"
LOG_FILE="app.log"

echo "🛑 Real Estate Manager 중지 중..."

# PID 파일 확인
if [ ! -f "$PID_FILE" ]; then
    echo "❌ PID 파일을 찾을 수 없습니다"
    echo "   애플리케이션이 실행되지 않았거나 이미 중지되었습니다"

    # 혹시 실행 중인 프로세스가 있는지 확인
    RUNNING_PID=$(pgrep -f "python main.py")
    if [ ! -z "$RUNNING_PID" ]; then
        echo "🔍 실행 중인 python main.py 프로세스 발견: $RUNNING_PID"
        echo "   강제 종료하시겠습니까? (y/N)"
        read -r response
        if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
            kill $RUNNING_PID
            echo "✅ 프로세스가 강제 종료되었습니다"
        fi
    fi
    exit 1
fi

# PID 읽기
PID=$(cat $PID_FILE)

# 프로세스가 실행 중인지 확인
if ! ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  프로세스가 이미 중지되었습니다 (PID: $PID)"
    rm -f $PID_FILE
    echo "🧹 PID 파일을 정리했습니다"
    exit 0
fi

# 프로세스 종료
echo "🔄 프로세스 중지 중... (PID: $PID)"
kill $PID

# 종료 확인 (최대 10초 대기)
for i in {1..10}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "✅ 애플리케이션이 성공적으로 중지되었습니다"
        rm -f $PID_FILE
        echo "🧹 PID 파일을 정리했습니다"
        exit 0
    fi
    echo "   대기 중... ($i/10)"
    sleep 1
done

# 강제 종료
echo "⚠️  일반 종료에 실패했습니다. 강제 종료를 시도합니다..."
kill -9 $PID

sleep 2
if ! ps -p $PID > /dev/null 2>&1; then
    echo "✅ 애플리케이션이 강제 종료되었습니다"
    rm -f $PID_FILE
    echo "🧹 PID 파일을 정리했습니다"
else
    echo "❌ 프로세스 종료에 실패했습니다"
    exit 1
fi