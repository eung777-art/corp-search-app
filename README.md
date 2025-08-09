# 기업 정보 검색 및 재무 분석 서비스

한국 기업의 corp_code를 검색하고 재무 정보를 시각화하는 웹 애플리케이션입니다.

## 기능

- 🔍 기업명으로 corp_code 검색
- 📊 DART API를 통한 재무 데이터 시각화
- 🤖 Gemini AI를 활용한 재무 분석

## 기술 스택

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML/CSS/JavaScript + Chart.js
- **APIs**: DART Open API, Google Gemini API

## 환경 변수

다음 환경 변수를 설정해야 합니다:

```
DART_API_KEY=your_dart_api_key
GEMINI_API_KEY=your_gemini_api_key
PORT=8080
DB_PATH=corp.db
```

## 로컬 실행

```bash
pip install -r requirements.txt
python app.py
```

## 배포

이 애플리케이션은 Render, Heroku 등 다양한 플랫폼에 배포할 수 있습니다.
