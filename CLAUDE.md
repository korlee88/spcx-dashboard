# SPCX Dashboard — Claude Code 작업 기록

## 작업 원칙 (중요)

**Claude가 직접 할 수 있는 작업은 모두 자율적으로 진행한다.**
- PR 생성 → 머지까지 직접 수행
- 커밋 & 푸시 직접 수행
- 수동 개입이 반드시 필요한 경우(브라우저 로그인, 시크릿 입력 등)에만 사용자에게 알린다

## 프로젝트 개요

GitHub Pages 기반 SpaceX(SPCX) 주간 분석 대시보드.
RKLB 대시보드(`korlee88/rklb-dashboard`)를 SPCX 종목으로 마이그레이션한 버전.
격일(월·수·금) KST 새벽 GitHub Actions가 자동으로 영상 자료를 생성한다(양산형 탈피: 영상마다 훅·관점·색상 변형).

- **저장소**: `korlee88/spcx-dashboard`
- **기본 브랜치**: `master`
- **원본 저장소**: `korlee88/rklb-dashboard` (Phase 1~2 완료 기반)

---

## SPCX 종목 특성

| 항목 | 값 |
|------|-----|
| 티커 | SPCX |
| 회사 | SpaceX |
| 산업 | 우주·발사체 |
| CEO | Elon Musk |
| 상장 | 2026-06-12 (나스닥, 공모가 $135) |
| 경쟁사 티커 | RKLB (Rocket Lab — 우주 섹터 비교) |
| 인도량 보고서 | 없음 (`has_delivery_reports: false`) |
| 실적 발표월 | 2, 5, 8, 11월 (예상 — 상장 직후, 첫 실적 8월 추정. 일정 공시 후 보정) |
| 베타 계수 | 2.0 (신규 상장 — 데이터 쌓이면 보정) |

---

## 아키텍처

```
spcx-dashboard/
├── .github/workflows/
│   ├── weekly-video.yml       # 주 1회 금요일 자동 실행
│   ├── auto-analysis.yml      # 매일 자동 분석
│   ├── backtest-run.yml       # 백테스트 (주 3회 자동 + 수동)
│   └── calendar-update.yml    # 매주 일정 갱신
├── config/
│   ├── ticker.json            # SPCX 종목 설정
│   └── rules.json             # R01~R26 규칙 엔진 (SPCX 특화)
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

## 마이그레이션 변경 사항 (RKLB → SPCX)

### config/ticker.json
- ticker, company_en/ko, industry_ko, brand_label → SPCX 값으로 교체
- competitor_ticker: `ASTS` → `RKLB` (동일 우주 섹터 비교)
- key_people: `["Peter Beck"]` → `["Elon Musk"]`
- has_delivery_reports: `false` (변경 없음)
- earnings_months: `[2,5,8,11]` (변경 없음 — 상장 직후 추정치, 일정 공시 후 보정)
- beta_coefficient: `2.2` → `2.0` (신규 상장 — 데이터 쌓이면 보정)
- youtube_search_queries, google_trends_keywords → SPCX/SpaceX/스타십/스타링크 키워드
- scene_wiki_articles → [SpaceX, Falcon 9] / [SpaceX Starship, Starbase] / [Starlink]
- image_future_tech_en (v1.3.0 신규) → 주간영상 이미지 프롬프트에 종목의 미래 기술·사업계획을
  주입하는 영어 문구. SPCX는 스타십(완전 재사용 슈퍼헤비)·스타링크·랩터엔진·화성/달 미션 등.
  `weekly_video_prep.py`의 `FUTURE_TECH_EN`이 읽어 3개 씬 프롬프트·지시문에 `{future_tech}`로 주입.

### config/rules.json
SPCX 우주·발사체 산업(스타십·팰컨·스타링크 중심)에 맞게 R01~R26 규칙 전면 재설계:
- R01: 발사 실패 (스타십/팰컨 9 실패·폭발)
- R04: 발사대 사고/화재 (스타베이스/케이프 커내버럴)
- R06: 경쟁사 대형 계약 (블루오리진/ULA/Rocket Lab/Amazon Kuiper — RKLB 포함)
- R07: 스타십 일정 장기 연기 (← 발사 장기 연기, 스타십 특화 / R25 동반 시 상쇄)
- R08: 머스크 SNS 논란 (← 피터 백 SNS 논란, 캡 ±2)
- R09: 대규모 증자·락업 해제 (← 대규모 유상증자, 신규 상장 락업 해제 물량 의미 추가)
- R14: 발사 성공 마일스톤 (스타십 궤도/부스터 캐치/팰컨 재사용 기록)
- R16: 대형 정부 계약 (NSSL/HLS/NRO)
- R17: 스타링크 대형 상업 계약 (← 대형 상업 계약, Starlink 특화)
- R18: 스타십 마일스톤 (← 뉴트론 마일스톤, 같은 R25 부스트 연계 유지)
- R19: 스타링크/스타실드 가입자·수주 급증
- R24: 머스크 사업 리스크 (테슬라·xAI 겸직 분산, 정치 행보, 캡 ±2)
- R25: 스타십 상업 운용 개시 (← 뉴트론 상업 론칭, +8pt 부스트 유지)
- R26: 팰컨 축소·스타십 전환 (← 소형 발사 사업 재편, R25 동반 시 0pt)

### 초기 설정 필요 사항
1. **씬 배경 이미지** (`data/scene-backgrounds/`) 교체
   - 현재 `scene_static_bg_files`는 전부 `null` → Wikipedia/AI 생성 폴백으로 정상 동작
   - SpaceX/스타십/스타링크 관련 이미지로 교체 시 3장 준비
2. **GitHub Secrets** 재설정 (rklb-dashboard에서 그대로 복사 가능)
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
  `RULE_LABELS` 맵(★config 미사용·자주 누락★), 매수지수 분해 라벨, 핵심인물 UI 라벨, `spcx_` 캐시키, 산문.
- **`SOURCE_INFO`(SourceTag, v1.3.0)**: 매체→국적·신뢰도 매핑은 **종목 무관**(언론사 기준)이라 그대로 복사한다.
  단 기업 IR 키 하나만 종목별로 교체 — SPCX는 `'spacex': ['기업공식(IR)', 'mid']` (RKLB는 `'rocket lab'`).

### 보존해야 할 레거시 내부 키 (변경 금지)
사용자에게 보이지 않고 동작은 종목 무관이며, 과거 데이터 호환·producer↔consumer 계약 때문에 **그대로 둔다**:
- `macroData.tsla`/`byd`, `prevTslaChg`, `tslaTrend3w`, `latestTslaPrice` (저장 데이터 alias)
- `muskX*`, `musk_x`, `optimusBoost`, `optimus_boost`, `newsCategories.Musk`, `catMuskDamp` (내부 변수·스키마 키)

### 검증
마이그레이션 후 반드시 감사 도구 실행 (잔재 + config 정합성 + RULE_LABELS 누락 자동 점검):
```bash
bash scripts/migration-audit.sh SPCX SpaceX 스페이스X 스타십 스타링크 "Elon Musk" 머스크 RKLB
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

## SPCX 규칙 엔진 특이사항

### R25 스타십 상업 운용 개시 부스트 (+8pt)
RKLB의 Neutron 규칙(R25)과 동일한 구조:
- scoring.js `calculateEnhancedScore`에서 R25 발동 시 buyIndex +8pt
- R07(스타십 일정 연기) + R25(스타십 상업 운용 준비) 동반 시: R07 영향 최소화, R25 +5pt 추가
- R26 단독(팰컨 축소): -3pt; R25 동반 시 0pt (전환 맥락으로 상쇄)

### `has_delivery_reports: false`
- `isDeliveryWeek()` 항상 false → 분기 인도량 발표주 증폭 없음
- 실적 발표주(`isEarningsWeek()`)는 earnings_months(2,5,8,11)로 정상 작동

### 경쟁사 비교 (RKLB)
- scoring.js layer [15] 경쟁사 상대강도: SPCX vs RKLB 주간 등락 비교
- RKLB 데이터 실패 시 파이프라인 계속 진행 (선택적 데이터)

---

## 주간 영상 TTS 설정

`scripts/weekly_video_make.py` 상단 상수로 제어 (tsla-dashboard PR #56과 동일 구조):

| 상수 | 값 | 설명 |
|------|-----|------|
| `VOICE` | `ko-KR-SunHiNeural` | edge-tts 음성 (밝은 여성, 친근 튜닝) |
| `RATE` | `+8%` | 발화 속도 |
| `PITCH` | `+6Hz` | 음 높이 |
| `LINE_PAUSE_MS` | `600` | 대본 줄(세그먼트) 사이 무음 휴지 (ms) |
| `TRIM_DB` | `-42.0` | 무음 판정 dBFS (가장자리 트리밍 임계값) |
| `TRIM_KEEP_MS` | `60` | 트리밍 후 가장자리에 남길 여유 무음 (ms) |
| `SCENE_LEAD_MS` | `500` | 씬 시작~첫 나레이션 사이 여유 무음 — 씬 전환 딜레이 (ms) |
| `SCENE_TAIL_MS` | `300` | 씬 끝 여유 무음 (ms) |

- `build_scene_tts_segments()`가 씬 대본을 줄 단위 세그먼트 리스트로 분리
  (씬0: 헤드라인·원인·호재·리스크 각각, 씬1: 헤드라인+세부줄, 씬2: 인트로+나머지줄).
- `gen_audio()`가 세그먼트마다 edge-tts MP3를 따로 생성하고 `_trim_edge_silence()`로
  가장자리 무음을 잘라낸 뒤, pydub `AudioSegment.silent(LINE_PAUSE_MS)`를 사이에 끼워 합성.
  합성 결과 앞 `SCENE_LEAD_MS`·뒤 `SCENE_TAIL_MS` 여유 무음을 덧붙여 export.
- `_trim_edge_silence()`: `detect_leading_silence`로 앞무음을, `piece.reverse()`로 뒷무음을
  측정해 양쪽 `TRIM_KEEP_MS`만 남기고 제거 (유효 구간 100ms 미만이면 원본 유지).
  edge-tts가 꼬리에 ~0.5초+ 자체 무음을 붙여 `LINE_PAUSE_MS`와 겹치면 체감 텀이 과도해지는
  문제를 해결 — 트리밍 + 600ms로 체감 ~720ms 일정하게 맞춘다.
- pydub/ffmpeg 미가용 시 공백으로 이어붙인 단일 TTS로 폴백 (휴지·트리밍 없음).
- 씬 전환(0.6초 크로스페이드) 직후 나레이션이 곧바로 시작되면 급한 느낌이 들어,
  `SCENE_LEAD_MS`(500ms)로 각 씬 첫머리에 숨 고를 틈을 둔다.

### 주간 영상 BGM (data/bgm.mp3)

- `data/bgm.mp3`: 저장소에 커밋된 배경음(원본 합성·CC0/로열티프리, ~63초 이음매 없는 루프).
  빌드 시 네트워크 의존 0 — `download_bgm()`은 이 파일 존재 여부만 확인해 반환한다.
- `scripts/make_bgm.py`: `data/bgm.mp3` 생성기. 따뜻한 메이저7 패드(C–Am–F–G) +
  아르페지오 + 약한 잔향을 numpy로 합성, `lameenc`로 MP3 인코딩(160kbps, mono).
  재생성: `python scripts/make_bgm.py`. 다른 트랙으로 교체하려면 `data/bgm.mp3`를
  원하는 파일로 덮어쓰고 커밋하면 된다.
- **v2(밋밋함 개선)**: 단일 사인파 패드가 어택 이후 ~3.5초간 완전히 평탄해 "밋밋하다"는
  피드백을 받음 → ① 코드톤을 디튠 유니즌 2voice(`DETUNE_CENTS`=5)로 합성해 천천히 비트(beat)치게
  함 ② 서브베이스에 코드당 2회 부풀어 오르는 펄스(`grain()`의 `pulse`)로 맥동하는 리듬감 추가
  ③ 전체 길이에 걸친 느린 밝기 LFO(`bright_full`, 0.045Hz)로 배음 비중이 계속 미세하게
  밝아지고 어두워짐 ④ 사이클마다 다른 `ARP_PATTERNS`로 4회 반복이 기계적으로 들리지 않게 함.
  RMS·스펙트럴 센트로이드의 시간축 표준편차가 기존 대비 약 1.7~1.9배로 증가(체감 움직임 증가),
  평균 라우드니스·전체 톤은 기존과 동일하게 유지.
- `build_video_async()`의 BGM 믹싱: `BGM_VOLUME`(0.10)로 볼륨 낮춘 뒤 영상 길이만큼
  루프. 같은 `AudioFileClip` 인스턴스를 재사용하면 리더 `start`가 공유돼 루프가
  깨지므로, 루프마다 새 클립을 생성한다 (`write` 이전에는 `close()` 호출 금지).
- 외부 CC0 음원 사이트(FreePD/archive.org/YouTube)는 빌드 환경에서 불안정하여
  채택하지 않음 — 원본 합성·커밋 방식으로 확정 (yt-dlp 의존 제거).

### 씬 구성 — AI 생성 고지 밴드 (씬 2)

마지막 씬(다음주 전망, idx 2) 이미지 **최하단 118px**에 반투명 다크 밴드(RGBA 10,14,26,205)로
AI 생성 고지 2줄을 30px 폰트·중앙 정렬·글자색 (170,180,202)으로 표기 (tsla-dashboard PR #58과 동일):

> 본 영상은 AI 분석 툴로 수집한 뉴스 자료를 분석해
> 핵심 내용을 요약·정리한 영상물입니다

- 위치: `weekly_video_prep.py` `build_scene_image()` 씬 2 분기 끝 (`return _apply_frame_overlay` 직전)
- **고지 문구는 script.json lines에 절대 넣지 않는다** — 이미지에만 그려서 TTS가 읽지 않게 한다.

### 격일 생성 & 양산형 탈피

- **생성 빈도**: `weekly-video.yml` cron `15 20,22 * * 0,2,4`(UTC 일·화·목 = KST 월·수·금 새벽).
  `load_week_sessions()`가 최근 `LOOKBACK_DAYS`(7일) **롤링 윈도우**라 격일로 돌려도 매번 다른 데이터.
  (격일 영상이 너무 비슷하면 `LOOKBACK_DAYS`를 4~5로 줄이면 더 또렷이 구분됨.)
- **오프닝 훅 다양화**: `HOOK_STYLES`(질문형·충격수치형·역발상형 등 8종) 중 생성일 시드로 1개 선택→
  `pick_hook()`이 `{hook_style}`로 프롬프트에 주입. "오늘의 뉴스"·"뉴스 N건 분석" 식 고정 오프닝 금지.
- **차별화 관점**: 프롬프트에 "시장 컨센서스와 다른 시각 1줄 필수"(단순 요약·낭독 탈피) 지시 추가.
- **색상 테마 로테이션**: `ACCENT_THEMES`(보라/시안/인디고 3종, 씬1 호재는 항상 초록) 중 `_theme_idx(생성일)`로
  선택 — **prep.py·make.py가 동일 함수로 계산해 정적 이미지·애니메이션 색상이 동기화**(인트로=썸네일 색 변형).
- **보류**: 자막 위치 변형은 레이아웃 깨짐 위험으로 미적용(필요 시 별도 작업).

### 대본 자체 검토(2차 패스)

`weekly_video_prep.py`의 `generate_script()`(1차 생성) 직후 `review_script()`를 거쳐
**1차 초안을 그대로 쓰지 않는다** — 같은 모델에 초안을 다시 보내 교열시킨 결과를 사용:

- 체크리스트(`REVIEW_PROMPT_TEMPLATE`): ① 반복 표현(같은 어미·핵심 단어가 여러 줄에서 기계적으로
  반복) ② 어색한 문구·번역체 ③ 미래 비전 전달력 — 씬2·이미지 프롬프트가 `FUTURE_TECH_EN`을
  충분히 구체적·인상적으로 전달하는지(막연하면 보강, 단 수치·사실은 새로 지어내지 않음).
- 1차 생성에 성공한 모델(`_last_model`)을 그대로 재사용(Opus 성공 시 Opus로 재검토, 아니면
  Gemini) — 다른 모델로 교열시키면 톤이 흔들릴 수 있어 동일 모델 유지.
- **안전망**: 재검토 응답에 `SCENE_0_TITLE:` 등 필수 마커가 하나라도 빠지면(형식 깨짐)
  1차 초안을 그대로 사용. API 예외 발생 시에도 1차 초안 유지. 재검토는 품질 보강용이며
  영상 생성 자체를 막아서는 안 되므로 항상 폴백 경로가 있다.
- 출력 형식은 1차와 완전히 동일(같은 마커 구조)이라 `parse_script()`/`parse_image_prompts()`를
  변경 없이 그대로 재사용한다.

---

## 앱 버전 히스토리

| 버전 | 날짜 | 주요 변경 |
|------|------|---------|
| **v1.5.0** | 2026-06-20 KST | 배경음악 밋밋함 개선 — `make_bgm.py` v2(디튠 유니즌 패드·펄싱 서브베이스·밝기 LFO·사이클별 아르페지오 변주, `data/bgm.mp3` 재생성) · 대본 2차 자체 검토 패스 추가(`review_script()` — 반복·어색한 문구·미래 비전 전달력 교열, 마커 누락/예외 시 1차 초안 폴백) · 클로징 씬 캘린더 일정 줄 날짜·제목 겹침 방지(두 줄 분리) |
| **v1.4.0** | 2026-06-18 KST | 쇼츠 양산형 탈피(rklb-dashboard v1.0.7 포팅) — 주1회→**격일(월·수·금 KST 새벽)** 생성 cron · 오프닝 훅 8종 풀(`HOOK_STYLES`/`pick_hook`, 생성일 시드로 선택, 고정 오프닝 금지) · 프롬프트에 "시장 컨센서스와 다른 차별화 관점 1줄" 필수화 · 인트로/썸네일 색상 테마 3종 로테이션(`ACCENT_THEMES`/`_theme_idx`, prep·make 동기화) |
| **v1.3.0** | 2026-06-17 KST | 뉴스 출처 국적·신뢰도 태그(`SourceTag` — 우주 전문매체 SpaceNews·NASASpaceflight·Space.com 등 `SOURCE_INFO`에 추가) · 주간영상 이미지 프롬프트에 미래 기술·사업계획(`image_future_tech_en`/`FUTURE_TECH_EN`) 주입 · 호재 씬 머리기호 ↑화살표→✓체크(`draw_check`) 전환 + 본문 폰트 50→46 축소 |
| **v1.2.0** | 2026-06-14 KST | 주간 영상 BGM 복원 — 원본 합성 배경음(`data/bgm.mp3`, `scripts/make_bgm.py`) 커밋해 네트워크 의존 0 · 씬 전환 직후 0.5초 나레이션 딜레이(`SCENE_LEAD_MS`/`SCENE_TAIL_MS`) · yt-dlp 의존 제거 |
| **v1.1.0** | 2026-06-12 KST | SPCX 마이그레이션(from rklb-dashboard v1.0.2) — RULE_LABELS·매수지수 분해 라벨·핵심인물(머스크) UI 전면 교체 · R01~R26 스타십/팰컨/스타링크 특화 규칙 · 캐시키 spcx_ 전환 |
| **v1.0.2** | 2026-06-11 KST | 보안 강화 — CDN 버전 고정+SRI(react/react-dom/babel 프로덕션 전환, tailwind 고정) · YouTube HttpError 로그 키 노출 차단 · GMAIL_TO 로그 제거 |
| **v1.0.1** | 2026-06-05 KST | 마이그레이션 잔재 정리(RULE_LABELS·UI 라벨·영상 프롬프트 RKLB화) · 영상 이미지 프롬프트 config 자동적응 · 마이그레이션 플레이북(MIGRATION.md)+감사도구 추가 |
| **v1.0.0** | 2026-06-05 KST | RKLB 마이그레이션 초기 릴리즈 (from tsla-dashboard v2.6.0) |

> 버전 업데이트 시 `index.html`의 `APP_VERSION` 상수와 이 표를 함께 수정할 것.
