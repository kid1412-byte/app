# 베이스 이미지 설정
FROM python:3.10

# 작업 디렉토리 생성
WORKDIR /app

# 필요한 파일 복사
COPY requirements.txt requirements.txt

# 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 컨테이너 실행 시 Flask 실행
CMD ["python", "app.py"]
