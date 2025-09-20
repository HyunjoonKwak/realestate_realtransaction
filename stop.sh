#!/bin/bash

# Real Estate Manager 강화된 중지 스크립트

APP_NAME="realestate_manager"
PID_FILE="app.pid"
LOG_FILE="app.log"
PORT=8080

echo "🛑 Real Estate Manager 완전 중지 중..."

# 함수: 포트를 사용하는 모든 프로세스 종료
kill_port_processes() {
    local port=$1
    echo "🔍 포트 ${port}를 사용하는 프로세스 확인 중..."

    # lsof로 포트 사용 프로세스 찾기
    local port_pids=$(lsof -ti :${port} 2>/dev/null)

    if [ -n "$port_pids" ]; then
        echo "📋 포트 ${port} 사용 프로세스 목록:"
        for pid in $port_pids; do
            local process_info=$(ps -p $pid -o pid,ppid,cmd --no-headers 2>/dev/null)
            if [ -n "$process_info" ]; then
                echo "   PID: $pid - $process_info"
            fi
        done

        echo "🔨 포트 ${port} 사용 프로세스들을 종료합니다..."
        echo $port_pids | xargs kill -9 2>/dev/null

        # 잠시 대기 후 재확인
        sleep 2
        local remaining_pids=$(lsof -ti :${port} 2>/dev/null)
        if [ -n "$remaining_pids" ]; then
            echo "⚠️  일부 프로세스가 남아있습니다. 재시도..."
            echo $remaining_pids | xargs kill -9 2>/dev/null
            sleep 1
        fi

        # 최종 확인
        local final_check=$(lsof -ti :${port} 2>/dev/null)
        if [ -z "$final_check" ]; then
            echo "✅ 포트 ${port}가 정리되었습니다"
        else
            echo "❌ 포트 ${port}에 여전히 프로세스가 남아있습니다"
        fi
    else
        echo "✅ 포트 ${port}에 실행 중인 프로세스가 없습니다"
    fi
}

# 함수: Python main.py 프로세스 모두 종료
kill_python_processes() {
    echo "🐍 Python main.py 프로세스 확인 중..."

    local python_pids=$(pgrep -f "python.*main\.py" 2>/dev/null)

    if [ -n "$python_pids" ]; then
        echo "📋 Python main.py 프로세스 목록:"
        for pid in $python_pids; do
            local process_info=$(ps -p $pid -o pid,ppid,cmd --no-headers 2>/dev/null)
            if [ -n "$process_info" ]; then
                echo "   PID: $pid - $process_info"
            fi
        done

        echo "🔨 Python main.py 프로세스들을 종료합니다..."
        echo $python_pids | xargs kill -9 2>/dev/null
        sleep 1

        # 재확인
        local remaining_python=$(pgrep -f "python.*main\.py" 2>/dev/null)
        if [ -z "$remaining_python" ]; then
            echo "✅ Python main.py 프로세스가 정리되었습니다"
        else
            echo "❌ 일부 Python 프로세스가 남아있습니다"
        fi
    else
        echo "✅ Python main.py 프로세스가 없습니다"
    fi
}

# 1단계: PID 파일 기반 종료 시도
if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    echo "📁 PID 파일 발견: $PID"

    if ps -p $PID > /dev/null 2>&1; then
        echo "🔄 PID 파일의 프로세스 종료 시도 (PID: $PID)"
        kill $PID 2>/dev/null

        # 5초 대기
        for i in {1..5}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                echo "✅ PID 파일의 프로세스가 종료되었습니다"
                break
            fi
            sleep 1
        done

        # 여전히 실행 중이면 강제 종료
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️  강제 종료 시도..."
            kill -9 $PID 2>/dev/null
        fi
    fi

    # PID 파일 제거
    rm -f $PID_FILE
    echo "🧹 PID 파일을 정리했습니다"
fi

# 2단계: 포트 기반 프로세스 종료
kill_port_processes $PORT

# 3단계: Python main.py 프로세스 종료
kill_python_processes

# 4단계: Flask 관련 프로세스 종료
echo "🌶️  Flask 관련 프로세스 확인 중..."
flask_pids=$(pgrep -f "flask" 2>/dev/null)
if [ -n "$flask_pids" ]; then
    echo "🔨 Flask 프로세스들을 종료합니다..."
    echo $flask_pids | xargs kill -9 2>/dev/null
fi

# 5단계: realestate_manager 관련 프로세스 종료
echo "🏠 realestate_manager 관련 프로세스 확인 중..."
app_pids=$(pgrep -f "$APP_NAME" 2>/dev/null)
if [ -n "$app_pids" ]; then
    echo "🔨 애플리케이션 프로세스들을 종료합니다..."
    echo $app_pids | xargs kill -9 2>/dev/null
fi

# 6단계: 백그라운드 작업 정리
echo "🧹 백그라운드 작업 정리 중..."
jobs -p | xargs kill 2>/dev/null

# 최종 확인
echo "🔍 최종 확인 중..."
final_port_check=$(lsof -ti :$PORT 2>/dev/null)
final_python_check=$(pgrep -f "python.*main\.py" 2>/dev/null)

if [ -z "$final_port_check" ] && [ -z "$final_python_check" ]; then
    echo "🎉 모든 프로세스가 성공적으로 정리되었습니다!"
    echo "✅ 포트 $PORT: 정리됨"
    echo "✅ Python 프로세스: 정리됨"
else
    echo "⚠️  일부 프로세스가 남아있을 수 있습니다:"
    if [ -n "$final_port_check" ]; then
        echo "   - 포트 $PORT: $final_port_check"
    fi
    if [ -n "$final_python_check" ]; then
        echo "   - Python: $final_python_check"
    fi
fi

echo "🏁 중지 스크립트 완료"