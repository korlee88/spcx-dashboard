# RKLB Dashboard — Claude Code 작업 기록

## 작업 원칙 (중요)

**Claude가 직접 할 수 있는 작업은 모두 자율적으로 진행한다.**
- PR 생성 → 머지까지 직접 수행
- 커밋 & 푸시 직접 수행
- 수동 개입이 반드시 필요한 경우(브라우저 로그인, 시크릿 입력 등)에만 사용자에게 알린다

## 프로젝트 개요

GitHub Pages 기반 Rocket Lab USA(RKLB) 주간 분석 대시보드.
TSLA 대시보드(`korlee88/tsla-dashboard`)를 RKLB 종목으로 마이그레이션한 버전.
주 1회 금요일 KST 새벽 GitHub Actions가 자동으로 영상 자료를 생성한다.

- **저장소**: `korlee88/rklb-dashboard`
- **기본 브랜치**: `master`
- **원본 저장소**: `korlee88/tsla-dashboard` (Phase 1~2 완료 기반)

---

## RKLB 종목 특성

| 항목 | 값 |
|------|-----|
| 티커 | RKLB |
| 회사 | Rocket Lab USA |
| 산업 | 우주·발사체 |
| CEO | Peter Beck |
| 경쟁사 티커 | ASTS (AST SpaceMobile — 우주 섹터 비교) |
| 인도량 보고서 | 없음 (`has_delivery_reports: false`) |
| 실적 발표월 | 2, 5, 8, 11월 |
| 베타 계수 | 2.2 (고변동성 성장주) |

---

## 아키텍처

```
rklb-dashboard/
├── .github/workflows/
│   ├── weekly-video.yml       # 주 1회 금요일 자동 실행
│   ├── auto-analysis.yml      # 하루 4회 자동 분석
│   ├── backtest-run.yml       # 백테스트 (매일 자동 + 수동)
│   └── calendar-update.yml    # 매주 일정 갱신
├── config/
│   ├── ticker.json            # RKLB 종목 설정
│   └── rules.json             # R01~R26 규칙 엔진 (RKLB 특화)
├── scripts/
│   ├── auto-analysis.js       # 뉴스 수집 & 분석 (Gemini)
│   ├── backtest-run.js        # 백테스트 (주간 주가 방향 매칭)
│   ├── calendar-update.js     # 이벤트 캘린더 갱신
│   ├── weekly_video_prep.py   # STEP 1: 대본 + 씬 이미지
│   ├── weekly_video_make.py   # STEP 2: TTS + 애니메이션 영상
│   ├── gws_publish.py         # STEP 5: YouTube/Sheets/Gmail 게시
│   ├── youtube_sentiment.py   # YouTube 관심도 수집
│   └── lib/
│       ├── prompt.js          # 시스템 프롬프트 빌더
│       └── scoring.js         # 다층 강화 채점 모델 v5.0
├── data/
│   ├── auto-sessions.json     # 최근 분석 세션 (빈 상태로 시작)
│   ├── backtest-results-2025.json
│   ├── backtest-results-2026.json
│   ├── calendar.json
│   ├── youtube-sentiment.json
│   └── scene-backgrounds/     # 씬 배경 이미지 (교체 필요)
├── index.html                 # 대시보드 (단일 파일 React)
├── package.json
├── requirements.txt
└── CLAUDE.md                  # 이 파일
```

---

## 마이그레이션 변경 사항 (TSLA → RKLB)

### config/ticker.json
- ticker, company_en/ko, industry_ko, brand_label → RKLB 값으로 교체
- competitor_ticker: `BYDDY` → `ASTS`
- key_people: `["Elon Musk"]` → `["Peter Beck"]`
- has_delivery_reports: `true` → `false`
- earnings_months: `[1,4,7,10]` → `[2,5,8,11]`
- beta_coefficient: `2.0` → `2.2`
- youtube_search_queries, google_trends_keywords → RKLB 키워드

### config/rules.json
RKLB 우주·발사체 산업에 맞게 R01~R26 규칙 전면 재설계:
- R01: 발사 실패 (launch failure)
- R04: 발사대 사고/화재
- R07: 발사 장기 연기
- R08: 피터 백 SNS 논란 (← 머스크 SNS 논란)
- R09: 대규모 유상증자 (← 보조금 축소)
- R14: 발사 성공 마일스톤 (← 인도 비트)
- R16: 대형 정부 계약 (NASA/DoD)
- R17: 대형 상업 계약 (constellation)
- R18: 뉴트론 마일스톤 (← FSD 마일스톤, 같은 R25 부스트 적용)
- R25: 뉴트론 상업 론칭 (← Optimus 상업화, +8pt 부스트)
- R26: 소형 발사 사업 재편 (← 차량 생산 축소)

### 초기 설정 필요 사항
1. **씬 배경 이미지** (`data/scene-backgrounds/`) 교체
   - RKLB/Neutron/Electron 관련 이미지 3장 준비
2. **GitHub Secrets** 재설정 (tsla-dashboard에서 그대로 복사 가능)
3. **GitHub Pages** 설정 (`master` 브랜치 root로)

---

## 다음 종목으로 마이그레이션 (중요)

> **전체 절차는 [`MIGRATION.md`](MIGRATION.md) 플레이북을 따른다.** 아래는 핵심 요약.

### Config 기반 원칙
이 저장소는 **config 기반 멀티 종목 템플릿**이다. 종목을 바꾸는 작업의 대부분은
코드가 아니라 **`config/ticker.json`(메타데이터) + `config/rules.json`(26규칙)** 값 교체다.

- **자동 (손댈 것 없음)**: `scripts/*` 전부, `.github/workflows/*` 전부.
  Node/Python이 config를 읽고, `index.html`도 런타임에 두 config를 `fetch`해 프롬프트·규칙을 생성한다.
- **수동 (직접 치환)**: `index.html`의 하드코딩 표면 — `gCfg` fallback, `SYSTEM_PROMPT` fallback,
  `RULE_LABELS` 맵(★config 미사용·자주 누락★), 매수지수 분해 라벨, 핵심인물 UI 라벨, `rklb_` 캐시키, 산문.

### 보존해야 할 레거시 내부 키 (변경 금지)
사용자에게 보이지 않고 동작은 종목 무관이며, 과거 데이터 호환·producer↔consumer 계약 때문에 **그대로 둔다**:
- `macroData.tsla`/`byd`, `prevTslaChg`, `tslaTrend3w`, `latestTslaPrice` (저장 데이터 alias)
- `muskX*`, `musk_x`, `optimusBoost`, `optimus_boost`, `newsCategories.Musk`, `catMuskDamp` (내부 변수·스키마 키)

### 검증
마이그레이션 후 반드시 감사 도구 실행 (잔재 + config 정합성 + RULE_LABELS 누락 자동 점검):
```bash
bash scripts/migration-audit.sh RKLB "Rocket Lab" 로켓랩 뉴트론 "Peter Beck" 피터백 ASTS
```

### GitHub 설정 함정 (Actions가 안 보일 때)
- **기본 브랜치**가 워크플로우 있는 브랜치(`master`)인지 — Actions는 기본 브랜치 워크플로만 인식.
- **Settings → Actions → General → "Allow all actions"** 활성화 여부.

---

## GitHub Secrets 필수 설정

| Secret | 용도 |
|--------|------|
| `GEMINI_API_KEY` | Gemini API (뉴스 분석, 자동 분석, 백테스트) |
| `ANTHROPIC_API_KEY` | Claude (주간 영상 대본 생성 1순위) |
| `YOUTUBE_API_KEY` | YouTube 관심도 수집 (선택) |

### GWS 통합 (선택)

| Secret | 용도 |
|--------|------|
| `GWS_YOUTUBE_TOKEN` | YouTube OAuth2 자동 업로드 |
| `GWS_SA_CREDENTIALS` | Google Sheets Service Account |
| `GOOGLE_SHEET_ID` | Sheets 문서 ID |
| `GMAIL_USER` | Gmail 발신 주소 |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 |
| `GMAIL_TO` | 수신자 이메일 |

---

## RKLB 규칙 엔진 특이사항

### R25 뉴트론 상업 론칭 부스트 (+8pt)
TSLA의 Optimus 규칙(R25)과 동일한 구조:
- scoring.js `calculateEnhancedScore`에서 R25 발동 시 buyIndex +8pt
- R07(발사대 손상) + R25(뉴트론 준비) 동반 시: R07 영향 최소화, R25 +5pt 추가
- R26 단독(소형 발사 축소): -3pt; R25 동반 시 0pt (전환 맥락으로 상쇄)

### `has_delivery_reports: false`
- `isDeliveryWeek()` 항상 false → 분기 인도량 발표주 증폭 없음
- 실적 발표주(`isEarningsWeek()`)는 earnings_months(2,5,8,11)로 정상 작동

### 경쟁사 비교 (ASTS)
- scoring.js layer [15] 경쟁사 상대강도: RKLB vs ASTS 주간 등락 비교
- ASTS 데이터 실패 시 파이프라인 계속 진행 (선택적 데이터)

---

## 주간 영상 TTS 설정

`scripts/weekly_video_make.py` 상단 상수로 제어 (tsla-dashboard PR #56과 동일 구조):

| 상수 | 값 | 설명 |
|------|-----|------|
| `VOICE` | `ko-KR-SunHiNeural` | edge-tts 음성 (밝은 여성, 친근 튜닝) |
| `RATE` | `+8%` | 발화 속도 |
| `PITCH` | `+6Hz` | 음 높이 |
| `LINE_PAUSE_MS` | `1000` | 대본 줄(세그먼트) 사이 무음 휴지 (ms) |

- `build_scene_tts_segments()`가 씬 대본을 줄 단위 세그먼트 리스트로 분리
  (씬0: 헤드라인·원인·호재·리스크 각각, 씬1: 헤드라인+세부줄, 씬2: 인트로+나머지줄).
- `gen_audio()`가 세그먼트마다 edge-tts MP3를 따로 생성한 뒤
  pydub `AudioSegment.silent(LINE_PAUSE_MS)`를 사이에 끼워 최종 MP3로 합성.
- pydub/ffmpeg 미가용 시 공백으로 이어붙인 단일 TTS로 폴백 (휴지 없음).

---

## 앱 버전 히스토리

| 버전 | 날짜 | 주요 변경 |
|------|------|---------|
| **v1.0.2** | 2026-06-11 KST | 보안 강화 — CDN 버전 고정+SRI(react/react-dom/babel 프로덕션 전환, tailwind 고정) · YouTube HttpError 로그 키 노출 차단 · GMAIL_TO 로그 제거 |
| **v1.0.1** | 2026-06-05 KST | 마이그레이션 잔재 정리(RULE_LABELS·UI 라벨·영상 프롬프트 RKLB화) · 영상 이미지 프롬프트 config 자동적응 · 마이그레이션 플레이북(MIGRATION.md)+감사도구 추가 |
| **v1.0.0** | 2026-06-05 KST | RKLB 마이그레이션 초기 릴리즈 (from tsla-dashboard v2.6.0) |

> 버전 업데이트 시 `index.html`의 `APP_VERSION` 상수와 이 표를 함께 수정할 것.
