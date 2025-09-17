#!/usr/bin/env python3
"""
국토교통부 실거래가 조회 시스템 메인 실행 파일
"""

import sys
import os
from src.web_app import ApartmentTrackerApp

def main():
    """메인 실행 함수"""
    print("🏠 국토교통부 실거래가 조회 시스템을 시작합니다.")
    print("📊 관심단지 추적 및 실거래가 분석 도구")
    print("=" * 50)

    # 웹 애플리케이션 시작
    app = ApartmentTrackerApp()
    app.run()

if __name__ == "__main__":
    main()
