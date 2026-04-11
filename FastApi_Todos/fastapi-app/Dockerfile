# Python 3.9 베이스 이미지 사용
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일만 먼저 복사 (레이어 캐시 활용)
COPY requirements.txt .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 필요한 소스 파일만 선택적으로 복사
COPY main.py .
COPY templates/ ./templates/
COPY static/ ./static/

# 비권한 유저 생성 및 전환 (root 실행 방지)
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

# FastAPI 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]