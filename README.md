# SPCX Dashboard

SpaceX (SPCX) 주간 주가 영향 분석 대시보드.  
GitHub Pages 기반 단일 파일 React 앱 + GitHub Actions 자동화.

🔗 **라이브**: https://korlee88.github.io/spcx-dashboard

---

## 빠른 시작 (Quick Setup)

### 1. GitHub Secrets 설정

저장소 → **Settings → Secrets and variables → Actions** → New repository secret

| Secret | 값 | 필수 |
|--------|-----|------|
| `GEMINI_API_KEY` | Google AI Studio API 키 | ✅ 필수 |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | ✅ 필수 (영상 대본) |
| `YOUTUBE_API_KEY` | YouTube Data API v3 키 | 선택 |
| `GWS_YOUTUBE_TOKEN` | YouTube OAuth2 token.json | 선택 |
| `GWS_SA_CREDENTIALS` | Google Service Account JSON | 선택 |
| `GOOGLE_SHEET_ID` | Google Sheets 문서 ID | 선택 |
| `GMAIL_USER` | Gmail 발신 주소 | 선택 |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 | 선택 |
| `GMAIL_TO` | 수신자 이메일 | 선택 |

### 2. GitHub Pages 활성화

저장소 → **Settings → Pages → Source: Deploy from a branch**  
Branch: `master` / Folder: `/ (root)` → **Save**

### 3. 첫 실행 확인

**Actions 탭** → `자동 분석` → `Run workflow` → 정상 동작 확인

---

## 자동화 스케줄

| 워크플로우 | 주기 | 설명 |
|------------|------|------|
| 자동 분석 | 매일 KST 10:00 | 뉴스 수집·분석·매수지수 계산 |
| 백테스트 | 월/수/금 KST 03:00 | 주간 주가 방향 예측 정확도 |
| 캘린더 | 매주 월요일 KST 09:00 | SPCX 이벤트 일정 갱신 |
| 주간 영상 | 매주 금요일 KST 05:15 | 대본·씬 이미지·TTS 영상 생성 |

---

## 아키텍처

```
spcx-dashboard/
├── config/
│   ├── ticker.json     # SPCX 종목 설정
│   └── rules.json      # R01~R26 규칙 엔진 (우주·발사체 특화)
├── scripts/            # GitHub Actions 실행 스크립트
├── data/               # 자동 생성 데이터 (Actions가 채움)
└── index.html          # 대시보드 (단일 파일 React)
```

자세한 내용은 [CLAUDE.md](CLAUDE.md) 참고.

---

## 종목 정보

| 항목 | 값 |
|------|-----|
| 티커 | SPCX |
| 회사 | SpaceX |
| CEO | Elon Musk |
| 산업 | 우주·발사체 |
| 경쟁사 비교 | RKLB (Rocket Lab) |
| 상장 | 2026-06-12 (나스닥, 공모가 $135) |
| 실적 발표 | 2·5·8·11월 (예상, 일정 공시 후 보정) |
