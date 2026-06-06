#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────
# migration-audit.sh — 종목 마이그레이션 검증 도구
#
# 새 종목으로 마이그레이션한 뒤 실행해서 ① 이전 종목 잔재, ② config 정합성을
# 자동 점검한다. MIGRATION.md Phase 7(검증)에서 사용.
#
# 사용법:
#   bash scripts/migration-audit.sh [이전종목_패턴 ...]
#
# 예) RKLB → 새 종목으로 옮긴 뒤, RKLB 잔재가 없는지 확인:
#   bash scripts/migration-audit.sh RKLB "Rocket Lab" 로켓랩 뉴트론 "Peter Beck" 피터백 ASTS
#
# 인자를 안 주면 잔재 검색은 건너뛰고 config 정합성만 점검한다.
# ──────────────────────────────────────────────────────────────────────────
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

RED=$'\033[0;31m'; GRN=$'\033[0;32m'; YLW=$'\033[1;33m'; CYN=$'\033[0;36m'; NC=$'\033[0m'
fail=0
SCAN_PATHS=(index.html scripts config package.json README.md CLAUDE.md)

echo "${CYN}━━━ 종목 마이그레이션 감사 ━━━${NC}"

# 0) 현재 종목 출력 ──────────────────────────────────────────────────────────
TICKER=$(node -e "console.log(require('./config/ticker.json').ticker)" 2>/dev/null)
COMPANY=$(node -e "console.log(require('./config/ticker.json').company_en)" 2>/dev/null)
echo "현재 종목: ${GRN}${TICKER} (${COMPANY})${NC}"
echo ""

# 1) 이전 종목 잔재 검색 ────────────────────────────────────────────────────
if [ "$#" -gt 0 ]; then
  echo "${CYN}[1] 이전 종목 잔재 검색${NC}  (하위호환 키 tsla/byd/musk/optimus 는 의도적 — 결과에서 제외)"
  for pat in "$@"; do
    # 하위호환/내부 레거시 키는 제외하고 검색
    hits=$(grep -rniE "$pat" "${SCAN_PATHS[@]}" 2>/dev/null \
      | grep -viE "tslaTrend|prevTsla|prev_tsla|latestTsla|macroData\.tsla|tsla:|byd|muskX|musk_x|optimusBoost|optimusR07|newsCategories|\.Musk|catMuskDamp" )
    if [ -n "$hits" ]; then
      cnt=$(echo "$hits" | wc -l)
      echo "  ${RED}✗ '${pat}' 잔재 ${cnt}건${NC}"
      echo "$hits" | sed 's/^/      /' | head -20
      fail=1
    else
      echo "  ${GRN}✓ '${pat}' 잔재 없음${NC}"
    fi
  done
else
  echo "${YLW}[1] 잔재 검색 건너뜀 (이전 종목 패턴 미입력)${NC}"
fi
echo ""

# 2) config 정합성 ──────────────────────────────────────────────────────────
echo "${CYN}[2] config 정합성${NC}"
RULE_COUNT=$(node -e "console.log(require('./config/rules.json').rules.length)" 2>/dev/null)
if [ "$RULE_COUNT" = "26" ]; then
  echo "  ${GRN}✓ rules.json 규칙 26개${NC}"
else
  echo "  ${RED}✗ rules.json 규칙 ${RULE_COUNT}개 (26개 기대)${NC}"; fail=1
fi

# ticker.json 필수 필드 존재
MISSING=$(node -e "
  const c=require('./config/ticker.json');
  const req=['ticker','company_en','company_ko','industry_ko','brand_label','repo','competitor_ticker','key_people','has_delivery_reports','earnings_months','scene_wiki_articles','google_trends_keywords'];
  console.log(req.filter(k=>c[k]===undefined).join(','));
" 2>/dev/null)
if [ -z "$MISSING" ]; then
  echo "  ${GRN}✓ ticker.json 필수 필드 모두 존재${NC}"
else
  echo "  ${RED}✗ ticker.json 누락 필드: ${MISSING}${NC}"; fail=1
fi
echo ""

# 3) index.html ↔ rules.json 라벨 정합성 (이번 마이그레이션에서 누락됐던 버그) ──
echo "${CYN}[3] index.html RULE_LABELS ↔ rules.json 정합성${NC}"
MISMATCH=$(node -e "
  const fs=require('fs');
  const rules=require('./config/rules.json').rules;
  const html=fs.readFileSync('index.html','utf-8');
  const m=html.match(/const RULE_LABELS = \{([\s\S]*?)\};/);
  if(!m){console.log('NO_RULE_LABELS');process.exit(0);}
  const block=m[1];
  const bad=[];
  for(const r of rules){
    // Rxx: 키가 라벨맵에 존재하는지
    const re=new RegExp('\\\\b'+r.id+'\\\\s*:');
    if(!re.test(block)) bad.push(r.id+'(없음)');
  }
  console.log(bad.join(','));
" 2>/dev/null)
if [ "$MISMATCH" = "NO_RULE_LABELS" ]; then
  echo "  ${YLW}△ RULE_LABELS 블록을 찾지 못함 (구조 변경됨?)${NC}"
elif [ -z "$MISMATCH" ]; then
  echo "  ${GRN}✓ R01~R26 모두 RULE_LABELS에 존재${NC}"
else
  echo "  ${RED}✗ RULE_LABELS 누락: ${MISMATCH}${NC}"; fail=1
fi
echo ""

# 4) 씬 배경 이미지 존재 ────────────────────────────────────────────────────
echo "${CYN}[4] 씬 배경 이미지${NC}"
BG_FILES=$(node -e "console.log((require('./config/ticker.json').scene_static_bg_files||[]).filter(Boolean).join(' '))" 2>/dev/null)
if [ -z "$BG_FILES" ]; then
  echo "  ${YLW}△ scene_static_bg_files 지정 없음 (전부 Wikipedia/AI 생성 사용)${NC}"
else
  for f in $BG_FILES; do
    if [ -f "data/scene-backgrounds/$f" ]; then
      echo "  ${GRN}✓ data/scene-backgrounds/$f 존재${NC}"
    else
      echo "  ${RED}✗ data/scene-backgrounds/$f 없음${NC}"; fail=1
    fi
  done
fi
echo ""

# 5) 스크립트 문법 검사 ─────────────────────────────────────────────────────
echo "${CYN}[5] 스크립트 문법${NC}"
for js in scripts/*.js scripts/lib/*.js; do
  node --check "$js" 2>/dev/null && echo "  ${GRN}✓ $js${NC}" || { echo "  ${RED}✗ $js 문법 오류${NC}"; fail=1; }
done
for py in scripts/*.py; do
  python3 -m py_compile "$py" 2>/dev/null && echo "  ${GRN}✓ $py${NC}" || { echo "  ${RED}✗ $py 문법 오류${NC}"; fail=1; }
done
echo ""

# 결과 ──────────────────────────────────────────────────────────────────────
if [ "$fail" = "0" ]; then
  echo "${GRN}━━━ ✅ 감사 통과 ━━━${NC}"
else
  echo "${RED}━━━ ❌ 문제 발견 — 위 항목 수정 필요 ━━━${NC}"
fi
exit $fail
