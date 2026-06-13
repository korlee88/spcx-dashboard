# 종목 마이그레이션 플레이북 (Migration Playbook)

> 이 저장소는 **config 기반 멀티 종목 템플릿**이다. 한 종목 대시보드를 다른 종목으로
> 옮기는 전 과정을 여기 정리한다. (실제 사례: `tsla-dashboard` → `rklb-dashboard`)
>
> **핵심 원칙**: 가능한 모든 것은 `config/`에서 제어된다. 하지만 `index.html`에는
> 마이그레이션 때 직접 치환해야 하는 **하드코딩 표면**이 남아 있다 — 이 문서의
> Phase 2가 그 지점을 빠짐없이 잡아주는 핵심이다.
>
> 마이그레이션 후 반드시 `bash scripts/migration-audit.sh <이전종목 패턴들>` 실행.

---

## 0. 난이도 지도 (어디가 쉽고 어디가 까다로운가)

| 영역 | 자동/수동 | 난이도 | 비고 |
|------|----------|--------|------|
| `config/ticker.json` | 수동 (값만) | ⭐ 쉬움 | 종목 메타데이터 단일 출처 |
| `config/rules.json` | 수동 (재설계) | ⭐⭐⭐ 보통 | 산업별 26규칙 재설계 — 가장 머리 쓰는 부분 |
| `scripts/*.js`, `*.py` | **대부분 자동** | ⭐ 쉬움 | config 읽음. 예외는 Phase 3 표 참고 |
| `.github/workflows/*` | **자동** | ⭐ 쉬움 | 손댈 것 없음 (config 기반) |
| `index.html` | 수동 (치환) | ⭐⭐ 주의 | 런타임은 config 기반이나 fallback·라벨·산문은 하드코딩 |
| 씬 배경 이미지 | 수동 | ⭐ 쉬움 | 이미지 3장 교체 |
| GitHub 설정 | 수동 | ⭐⭐ 함정 | 기본 브랜치·Actions 활성화에서 막히기 쉬움 (Phase 6) |

**요약**: 두뇌 노동은 `rules.json`(규칙 재설계)에, 실수 위험은 `index.html`(누락)과
GitHub 설정(보이지 않는 함정)에 있다. 나머지는 거의 자동이다.

---

## 1. 동작 아키텍처 (왜 대부분 자동인가)

```
config/ticker.json ─┐
                    ├─► scripts/lib/prompt.js ─► buildSystemPrompt() ─► auto-analysis.js / backtest-run.js
config/rules.json ──┘                                                    (GitHub Actions에서 실행)
        │
        └─► index.html이 런타임에 fetch():
              fetch('./config/ticker.json') → gCfg
              fetch('./config/rules.json')  → buildSystemPromptBrowser(), buildRulesMetaFromCfg()
```

- **Node 스크립트**(분석·백테스트·캘린더)는 `loadTickerConfig()`/`loadRulesConfig()`로 config를 읽는다 → 종목 바꿔도 코드 수정 불필요.
- **`index.html`**도 브라우저에서 두 config를 `fetch`해서 시스템 프롬프트·규칙 메타를 **런타임 생성**한다.
  - 그래서 `index.html` 안의 `const SYSTEM_PROMPT`, `const RULE_LABELS`, `gCfg` 등은
    **fetch 실패 시 fallback** 또는 **config에서 안 만들어지는 표시 문자열**이다.
    → 동작엔 문제 없어 보여도 사용자에게 옛 종목 라벨이 노출될 수 있으니 **반드시 함께 치환**한다.

> ⚠️ **이번 마이그레이션에서 실제로 누락됐던 버그**: `RULE_LABELS` 맵의 절반이 TSLA 라벨로
> 남아 대시보드에 "인도량 미달", "머스크 자사주매입" 등이 표시됐다. `scripts/migration-audit.sh`의
> [3]번 검사가 바로 이 유형을 자동으로 잡는다.

---

## 2. Phase별 절차

### Phase 0 — 새 저장소 준비

1. 새 GitHub 저장소 생성: `korlee88/<newticker>-dashboard`
2. 이 저장소(또는 가장 최신 종목 저장소) 내용을 새 저장소로 복사.
3. 작업 브랜치 생성 후 진행 → PR로 머지.

### Phase 1 — `config/ticker.json` (값만 교체) ⭐

아래 표대로 값을 바꾼다. **코드는 건드리지 않는다.**

| 필드 | 의미 | 예시 (RKLB) |
|------|------|-------------|
| `ticker` | 티커 | `"RKLB"` |
| `company_en` / `company_ko` | 영문/한글 회사명 | `"Rocket Lab USA"` / `"로켓랩"` |
| `industry_ko` | 산업 (영상·프롬프트에 사용) | `"우주·발사체"` |
| `brand_label` | 영상 브랜드 라벨 | `"RKLB WEEKLY"` |
| `repo` | `owner/repo` | `"korlee88/rklb-dashboard"` |
| `beta_coefficient` | 베타(변동성) | `2.2` |
| `competitor_ticker` | 비교 경쟁사 티커 | `"ASTS"` |
| `key_people` | 핵심 인물(SNS 신호) | `["Peter Beck"]` |
| `has_delivery_reports` | 분기 인도량 발표 종목 여부 | `false` |
| `earnings_months` | 실적 발표월 | `[2,5,8,11]` |
| `scene_wiki_articles` | 씬별 위키 이미지 후보 **+ 주간영상 이미지 프롬프트의 기체·제품명** | `[["Rocket Lab",...],...]` |
| `scene_static_bg_files` | 씬별 고정 배경 (없으면 `null`) | `[null,"bg_scene_02.jpg",null]` |
| `youtube_search_queries` | 유튜브 관심도 검색어 | `["Rocket Lab RKLB stock",...]` |
| `google_trends_keywords` | 구글 트렌드 키워드 | `["로켓랩","RKLB",...]` |
| `video_title_template` / `video_tags` / `email_subject_template` | 영상·메일 템플릿 | `{ticker}`,`{date}` 등 치환자 사용 |

> `has_delivery_reports: false` → 인도량 발표주 증폭 로직(`isDeliveryWeek`)이 항상 false가 되어
> 자동으로 비활성화된다. 인도량 보고가 있는 종목(예: 자동차)은 `true`.
>
> `scene_wiki_articles`는 위키 배경 이미지 후보일 뿐 아니라 `weekly_video_prep.py`가
> **주간영상 씬별 이미지 프롬프트의 핵심 기체·제품명**으로도 사용한다(씬0/1/2 순서대로 주입).
> 따라서 **반드시 해당 종목 자신의 발사체·제품**으로 채운다(예: SpaceX → Falcon 9 / Starship / Starlink).
> 프롬프트에는 "경쟁사·타사 로켓 금지" 가드레일이 자동 포함되어, 경쟁사 뉴스가 많은 주에도
> 경쟁사 기체가 배경으로 그려지지 않는다.

### Phase 2 — `config/rules.json` (산업별 26규칙 재설계) ⭐⭐⭐

가장 핵심적인 두뇌 노동. **규칙 ID(R01~R26)와 개수(26개)는 유지**하되, 각 규칙의
`name_ko`/`desc`/`direction`/`cat`을 새 종목 산업에 맞게 재정의한다.

**⚠️ 특수 처리되는 규칙 ID는 의미를 보존할 것** (scoring.js가 ID로 분기함):

| ID | 특수 동작 (scoring.js) | 새 종목에서 매핑할 의미 |
|----|----------------------|----------------------|
| **R25** | 강세 부스트 **+8pt** (`optimusBoost` 레이어) | 그 종목의 **최대 장기 성장 촉매** (RKLB=뉴트론 상업 론칭, TSLA=옵티머스) |
| **R07** | R25와 동반 시 페널티 최소화 | 부정 이벤트지만 R25 전환 맥락이면 상쇄 (RKLB=발사 연기) |
| **R26** | 단독 약세 / R25 동반 시 0 | 전환기 사업 재편 (RKLB=소형발사 축소, TSLA=차량생산 조정) |
| **R08 / R24** | 핵심인물 SNS·리스크 (캡 ±2) | `key_people` 관련 규칙 |

나머지 필드:
- `system_prompt_intro` — `{company_en}`,`{ticker}` 치환자 사용 → 종목 무관, 손댈 것 없음
- `scoring_guidelines` — `{company_en}`,`{ticker}` 치환자 사용 → 산업 예시 문구만 다듬기
- `per_rule_caps` — 규칙별 점수 상한. 재설계한 규칙에 맞게 갱신 (이 텍스트가 AI에 그대로 전달됨)
- `direction_rule` — 종목 무관, 손댈 것 없음

### Phase 3 — 스크립트 (대부분 자동, 예외만 확인) ⭐

**손댈 것 없음** (config 기반): `auto-analysis.js`, `backtest-run.js`, `calendar-update.js`,
`youtube_sentiment.py`, `gws_publish.py`, `weekly_video_make.py`, `lib/prompt.js`, `lib/scoring.js`,
그리고 `.github/workflows/*` 전부.

**확인만 하면 되는 곳** (이미 config/placeholder로 정리됨):
- `weekly_video_prep.py` 이미지 프롬프트 예시 → `{company_ko}`·`{industry_ko}` 치환자로 자동 적응.
  단, **씬 분위기/색감 예시 문구**가 새 산업에 어색하면 다듬어도 좋다 (선택).

**의도적으로 종목명이 안 박혀 있어도 그대로 두는 레거시 내부 키** (변경 불필요·금지):

| 위치 | 키 | 이유 |
|------|-----|------|
| scoring.js / auto-analysis.js | `macroData.tsla`, `byd`, `prevTslaChg`, `tslaTrend3w`, `latestTslaPrice` | 과거 저장 데이터 하위호환 alias |
| auto-analysis.js | `muskXData`, `muskXSentiment`, `muskXAdj` | 핵심인물 감성의 내부 변수/데이터 키 (함수는 `key_people` 기반) |
| scoring.js / index.html | `optimusBoost`, `optimus_boost`, `optimusR07Offset` | R25 부스트 레이어의 내부 키 (표시 라벨은 Phase 2에서 교체) |
| scoring.js | `newsCategories.Musk`, `catMuskDamp` | 핵심인물 뉴스 카테고리 스키마 키 (producer↔consumer 공유) |

> 이 키들은 **사용자에게 보이지 않는다.** 이름만 옛 종목이고 동작은 종목 무관이다.
> 바꾸려면 producer(생성)와 consumer(소비)를 동시에 고쳐야 하고 과거 데이터 호환이 깨지므로 **건드리지 않는다.**

### Phase 4 — `index.html` 하드코딩 표면 (치환) ⭐⭐

런타임은 config를 fetch하지만, 아래 지점들은 **하드코딩**이라 직접 바꿔야 한다.
줄 번호는 버전마다 바뀌므로 **검색 문자열(앵커)** 로 찾는다.

| 앵커 (검색어) | 내용 | 처리 |
|--------------|------|------|
| `const APP_VERSION` | 버전·날짜·changelog | 새 버전 1줄로 교체 (연혁상 "from xxx-dashboard" 언급은 남겨도 OK) |
| `tailwind ... rklb:` (`rklb: { orange:` ) | 브랜드 색상 객체 | 새 종목 색으로 교체 (선택, 미관) |
| `let gCfg = {` | config fetch 실패 시 **fallback 값** | 새 종목 값으로 교체 |
| `const SYSTEM_PROMPT =` | fetch 실패 시 **fallback 프롬프트** | 회사명·Per-rule CAPS를 rules.json과 동기화 |
| `const RULE_LABELS = {` | **규칙 단축 라벨맵** (config 미사용!) | rules.json `name_ko`와 R01~R26 전부 일치 ★자주 누락★ |
| `const labels = { base:` | 매수지수 분해 **표시 라벨** | `optimus_boost`/`musk_x` 등 표시 문자열만 새 종목어로 |
| `X 동향` / `🐦` | 핵심인물 SNS UI 라벨 | `key_people`에 맞게 (예: 머스크→피터백) |
| 캐시키 `rklb_` | localStorage 키 접두사 (약 16곳) | `sed`로 `<old>_` → `<new>_` 일괄 치환 |
| 산문 텍스트 | 백테스트 인사이트·가이드의 종목 고유 설명 | 산업 맥락에 맞게 수정 |

**일괄 치환 시작점** (정밀 확인 전 1차 스윕):
```bash
# 회사/티커/인물/제품 키워드를 새 종목으로 (예시 — 실제 값으로 바꿔 실행)
sed -i 's/RKLB/XYZ/g; s/Rocket Lab USA/New Co/g; s/로켓랩/뉴코/g; s/rklb_/xyz_/g' index.html
```
> sed 1차 스윕 후에도 **반드시 Phase 7 감사**로 누락(특히 RULE_LABELS·산문·인물명)을 잡는다.

### Phase 5 — 에셋 & 데이터 초기화

**씬 배경 이미지** — `data/scene-backgrounds/` 의 `scene_static_bg_files`에 지정된 이미지를
새 종목용으로 교체. (없으면 위키/AI 생성으로 대체되므로 필수는 아님)

**`package.json`** — `name`,`description`,`homepage` 교체.

**데이터 파일 초기화** — 과거 종목 데이터를 비운다 (`data/README.md` 참고):
```bash
echo '{"sessions":[],"lastUpdated":""}' > data/auto-sessions.json
echo '{"events":[],"lastUpdated":""}'   > data/calendar.json
echo '{"weeks":[],"lastUpdated":""}'    > data/backtest-results-2025.json
echo '{"weeks":[],"lastUpdated":""}'    > data/backtest-results-2026.json
echo '{"score":0,"video_count":0,"total_views":0,"velocity_label":"","lastUpdated":""}' > data/youtube-sentiment.json
```

### Phase 6 — GitHub 설정 (보이지 않는 함정 주의) ⭐⭐

> **이 단계에서 가장 많이 막힌다.** 워크플로우 파일이 있어도 Actions 탭에 안 보이는
> 두 가지 원인이 있다 — 아래 3·4번을 반드시 확인.

1. **Secrets** — `Settings → Secrets and variables → Actions`
   - 필수: `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`
   - 선택: `YOUTUBE_API_KEY`, GWS 계열(`GWS_YOUTUBE_TOKEN`,`GWS_SA_CREDENTIALS`,`GOOGLE_SHEET_ID`,`GMAIL_*`)
   - 이전 종목 저장소에서 그대로 복사 가능.
2. **GitHub Pages** — `Settings → Pages → Deploy from a branch` → `master` / `/(root)` → Save
3. **⚠️ 기본 브랜치** — `Settings`(General) → Default branch가 **워크플로우가 있는 브랜치(master)** 인지 확인.
   - GitHub Actions는 **기본 브랜치의 워크플로만 인식**한다. 기본 브랜치가 개발 브랜치로 되어 있으면
     `.github/workflows/*`가 있어도 Actions 탭에 안 뜬다. (이번에 실제로 막혔던 지점)
4. **⚠️ Actions 권한** — `Settings → Actions → General → Actions permissions`
   → **"Allow all actions and reusable workflows"** 선택 후 Save.
   - 비활성화 상태면 "Dependency Graph", "pages-build-deployment"만 보이고 커스텀 워크플로는 숨겨진다.
5. 재확인: `Actions` 탭에 4개 워크플로(자동 분석·백테스트·캘린더·주간 영상)가 보이면 정상.
   `자동 분석` → `Run workflow`로 첫 실행 테스트.

### Phase 7 — 검증 ✅

```bash
# 이전 종목 패턴을 인자로 넘겨 잔재 + config 정합성 일괄 점검
bash scripts/migration-audit.sh RKLB "Rocket Lab" 로켓랩 뉴트론 "Peter Beck" 피터백 ASTS
```

감사 스크립트가 점검하는 항목:
1. **이전 종목 잔재** (하위호환 키는 자동 제외)
2. `rules.json` 규칙 26개 / `ticker.json` 필수 필드
3. **`index.html` RULE_LABELS ↔ rules.json 정합성** (절반 누락 버그 탐지)
4. 씬 배경 이미지 존재
5. 전 스크립트 문법

> **정상으로 봐도 되는 잔재**: `CLAUDE.md`·`MIGRATION.md`의 마이그레이션 연혁 설명,
> `APP_VERSION` changelog의 "from <이전>-dashboard" 출처 표기는 **의도된 기록**이다.
> 코드·UI 라벨·산문에서의 잔재만 수정 대상.

---

## 3. 빠른 체크리스트 (복붙용)

```
[ ] config/ticker.json  — 전 필드 새 종목 값으로 (Phase 1 표)
[ ] config/rules.json   — R01~R26 재설계, R25/R07/R26/R08/R24 특수의미 보존 (Phase 2)
[ ] index.html          — APP_VERSION / gCfg / SYSTEM_PROMPT / RULE_LABELS / labels / 인물라벨 / rklb_ 캐시키
[ ] 씬 배경 이미지       — data/scene-backgrounds/ 교체
[ ] package.json        — name/description/homepage
[ ] data/*.json         — 초기화 (Phase 5)
[ ] GitHub Secrets      — GEMINI/ANTHROPIC (필수)
[ ] GitHub 기본 브랜치   — master 확인 (Actions 인식 조건)
[ ] GitHub Actions 권한  — Allow all 활성화
[ ] GitHub Pages        — master/root
[ ] bash scripts/migration-audit.sh <이전종목...>  → ✅ 통과
[ ] Actions 탭 4개 워크플로 확인 + 자동분석 1회 수동 실행
```
