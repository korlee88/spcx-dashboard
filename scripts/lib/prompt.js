/**
 * 시스템 프롬프트 빌더 — config/rules.json + config/ticker.json 기반
 * Node.js 스크립트(auto-analysis, backtest-run)에서 공통 사용
 */

const fs   = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..', '..');

function loadTickerConfig(cfgPath) {
  const p = cfgPath || path.join(ROOT, 'config', 'ticker.json');
  return JSON.parse(fs.readFileSync(p, 'utf-8'));
}

function loadRulesConfig(cfgPath) {
  const p = cfgPath || path.join(ROOT, 'config', 'rules.json');
  return JSON.parse(fs.readFileSync(p, 'utf-8'));
}

/**
 * rules.json + ticker.json을 조합해 AI에 전달할 SYSTEM_PROMPT 문자열 조립.
 * {company_en}, {ticker} 플레이스홀더를 치환한다.
 */
/**
 * ipo_fact_en(선택, ticker.json) 치환 후 반환 — 없으면 빈 문자열.
 * 상장 직후 종목처럼 모델의 사전 학습 지식(비상장 시절)과 대시보드 전제(상장 완료)가
 * 충돌하는 경우에만 ticker.json에 설정. buildSystemPrompt뿐 아니라 Google Search
 * grounding으로 별도 프롬프트를 만드는 호출부(뉴스/이벤트 수집)에서도 재사용한다 —
 * 실시간 검색 결과는 "실제로는 비상장"이라는 현실을 그대로 반영해 전제와 충돌하기 쉽다.
 */
function ipoFactNote(cfg) {
  if (!cfg.ipo_fact_en) return '';
  return cfg.ipo_fact_en
    .replace(/\{company_en\}/g, cfg.company_en)
    .replace(/\{ticker\}/g, cfg.ticker);
}

function buildSystemPrompt(cfg, rulesData) {
  const sub = (str) => str
    .replace(/\{company_en\}/g, cfg.company_en)
    .replace(/\{ticker\}/g, cfg.ticker);

  const ruleRef = rulesData.rules
    .map(r => `${r.id}=${r.desc}`)
    .join(', ');

  const ipoFact = ipoFactNote(cfg);
  const lines = [sub(rulesData.system_prompt_intro)];
  if (ipoFact) lines.push('', ipoFact);
  lines.push(
    '',
    'Rule reference:',
    ruleRef,
    '',
    sub(rulesData.scoring_guidelines),
    '',
    rulesData.per_rule_caps,
    '',
    rulesData.direction_rule,
  );
  return lines.join('\n');
}

/**
 * index.html 브라우저 측에서 fetch로 로드한 rules/ticker 객체를 받아
 * SYSTEM_PROMPT 문자열을 조립하는 함수 (Node require 없이 동작).
 * 위 buildSystemPrompt와 완전히 동일한 로직 — 브라우저 전용.
 */
function buildSystemPromptBrowser(cfg, rulesData) {
  if (!cfg || !rulesData) return null;
  return buildSystemPrompt(cfg, rulesData);
}

module.exports = { loadTickerConfig, loadRulesConfig, buildSystemPrompt, buildSystemPromptBrowser, ipoFactNote };
