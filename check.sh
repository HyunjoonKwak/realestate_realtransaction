#!/bin/bash

# Real Estate Manager 상태 확인 스크립트

APP_NAME="realestate_manager"
PID_FILE="app.pid"
LOG_FILE="app.log"
PORT=8080

echo "🔍 Real Estate Manager 상태 확인 중..."
echo ""

# PID 파일 확인
if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    echo "📄 PID 파일 발견: $PID"

    # 프로세스 실행 여부 확인
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 애플리케이션이 실행 중입니다 (PID: $PID)"

        # 프로세스 상세 정보
        echo ""
        echo "📊 프로세스 정보:"
        ps -p $PID -o pid,ppid,cmd,etime,pcpu,pmem

        # 포트 확인
        echo ""
        echo "🌐 네트워크 상태:"
        if lsof -i :$PORT > /dev/null 2>&1; then
            echo "✅ 포트 $PORT 에서 서비스 중"
            lsof -i :$PORT
        else
            echo "⚠️  포트 $PORT 가 열려있지 않습니다"
        fi

        # 웹 서비스 응답 확인
        echo ""
        echo "🏥 서비스 상태 확인:"
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT > /tmp/status_code; then
            STATUS_CODE=$(cat /tmp/status_code)
            if [ "$STATUS_CODE" = "200" ]; then
                echo "✅ 웹 서비스 정상 응답 (HTTP $STATUS_CODE)"
            else
                echo "⚠️  웹 서비스 비정상 응답 (HTTP $STATUS_CODE)"
            fi
            rm -f /tmp/status_code
        else
            echo "❌ 웹 서비스 응답 없음"
        fi

    else
        echo "❌ PID 파일은 있지만 프로세스가 실행되지 않습니다"
        echo "🧹 오래된 PID 파일을 정리하세요: rm $PID_FILE"
    fi
else
    echo "❌ PID 파일이 없습니다"

    # 포트로 프로세스 찾기
    echo ""
    echo "🔍 포트 $PORT 에서 실행 중인 프로세스 확인:"
    if lsof -i :$PORT > /dev/null 2>&1; then
        echo "⚠️  포트 $PORT 에서 다른 프로세스가 실행 중입니다:"
        lsof -i :$PORT
    else
        echo "❌ 포트 $PORT 에서 실행 중인 프로세스가 없습니다"
    fi
fi

# 로그 파일 확인
echo ""
echo "📋 로그 파일 상태:"
if [ -f "$LOG_FILE" ]; then
    echo "✅ 로그 파일 존재: $LOG_FILE"
    echo "   파일 크기: $(ls -lh $LOG_FILE | awk '{print $5}')"
    echo "   최근 수정: $(ls -l $LOG_FILE | awk '{print $6, $7, $8}')"
    echo ""
    echo "📝 최근 로그 (마지막 10줄):"
    tail -10 $LOG_FILE
else
    echo "⚠️  로그 파일이 없습니다: $LOG_FILE"
fi

echo ""
echo "🛠️  유용한 명령어:"
echo "   앱 시작: ./start.sh"
echo "   앱 중지: ./stop.sh"
echo "   실시간 로그: tail -f $LOG_FILE"
echo "   웹 접속: http://localhost:$PORT"