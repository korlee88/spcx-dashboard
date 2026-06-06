# data/ — 자동 생성 데이터

이 디렉터리의 JSON은 대부분 **GitHub Actions가 자동으로 채우고 커밋**한다.
새 종목 마이그레이션 시에는 [초기 상태로 비운다](../MIGRATION.md#phase-5--에셋--데이터-초기화).

| 파일 | 생성 주체 | 초기값 | 설명 |
|------|----------|--------|------|
| `auto-sessions.json` | `auto-analysis.js` (하루 4회) | `{"sessions":[],"lastUpdated":""}` | 뉴스 분석·매수지수 세션 기록 |
| `calendar.json` | `calendar-update.js` (주 1회) | `{"events":[],"lastUpdated":""}` | 종목 이벤트 일정 |
| `backtest-results-2025.json` | `backtest-run.js` (매일) | `{"weeks":[],"lastUpdated":""}` | 2025년 주간 예측 정확도 |
| `backtest-results-2026.json` | `backtest-run.js` (매일) | `{"weeks":[],"lastUpdated":""}` | 2026년 주간 예측 정확도 |
| `youtube-sentiment.json` | `youtube_sentiment.py` (하루 4회) | `{"score":0,"video_count":0,"total_views":0,"velocity_label":"","lastUpdated":""}` | 유튜브 관심도 |
| `weekly-report/<날짜>/` | `weekly_video_prep.py` (주 1회 금) | — | 주간 영상 대본·씬 이미지 (MP3/MP4는 커밋 제외, 아티팩트로 보관) |

## scene-backgrounds/

씬별 고정 배경 이미지. `config/ticker.json`의 `scene_static_bg_files`에서 참조한다.
지정이 `null`인 씬은 위키피디아 이미지 또는 AI 생성으로 대체된다.

> ⚠️ 현재 `bg_scene_02/03/04.jpg`는 **이전 종목(TSLA)에서 가져온 임시 플레이스홀더**다.
> RKLB(우주·발사체) 분위기 이미지로 교체 권장. 교체 전까지 영상 품질에만 영향.

## frame-template.png (선택)

`scripts/generate_frame.py`로 1회 생성하는 영상 공통 외곽 프레임(투명 중앙).
없어도 영상 파이프라인은 동작한다. 새 디자인이 필요할 때만 재생성 후 커밋.
