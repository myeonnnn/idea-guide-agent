# 아이디어 검증 & 로드맵 에이전트

아이디어 입력부터 시장조사, 가설 검증, MVP/MLP 목표 설정, 비즈니스모델 가정까지 전 과정을 안내하는 대화형 AI 에이전트.

## 왜 만드는가

기존 "AI 아이디어 검증 도구"(ValidatorAI, IdeaProof, DimeADozen, FounderPal 등)는 빠른 리포트 생성에 최적화되어 있고, 결과물의 사실 검증 장치가 약하다. LLM이 생성한 시장 규모/통계/근거가 검증 없이 그럴듯하게 제시되는 경우가 많다.

핵심 원칙: **"모르는 것보다 잘못된 정보를 주는 것이 더 나쁘다"** — 확인 안 된 정보는 추정/미확인으로 명확히 라벨링한다.

## 이 프로젝트가 하는 것 / 하지 않는 것

- **한다**: 아이디어를 입력받아 타겟층 설정 → 시장조사 → 가치제안·차별화 → 가설 수립 → 가설 검증(리스키스트 어썸션 우선순위화) → MVP/MLP 정의 → 비즈니스모델 가정 → 종합 판단(진행/피벗/보류), 8단계 파이프라인을 거쳐 **검증된 텍스트/JSON 초안(로드맵 문서)** 을 생성한다. 결과는 마크다운 파일로 저장할 수 있다.
- **하지 않는다**: 그 초안에 담긴 아이디어(예: "반려동물 산책 매칭 앱")를 실제 코드/제품으로 구현하지 않는다. 이 도구의 산출물은 어디까지나 다음 의사결정을 위한 초안이다. "만들지 말지, 무엇을 만들지"를 결정하는 상류(upstream) 검증 단계이며, PRD 작성이나 실제 개발(Manyfast, Cursor, Claude Code 등)은 이후 단계에서 사람이 이 초안을 들고 넘어가는 영역이다.

## 핵심 차별화: 자가검증(Self-verification) 루프

- **출처 등급화**: 1차 자료(공식 통계/학술자료) vs 2차 해석 vs AI 추정치를 구분해서 라벨링
- **신뢰도 명시**: 모든 수치/주장에 확신도 표기, 미확인 정보는 "추정" 또는 "확인 필요"로 명확히 구분
- **재현 가능한 근거**: 결과물에 출처 링크 항상 첨부

## 아키텍처 요약

- 로컬 전용(127.0.0.1), 외부 API 키 없이 로컬 `claude` CLI(Claude Code)를 추론 엔진으로 사용
- 백엔드: Python/FastAPI. 파이프라인 오케스트레이션과 자가검증 로직은 코드로 구현(스킬/프롬프트 지시문에만 의존하지 않음)
- 프론트엔드: Vite + React + TypeScript (`frontend/`). 개발 시 Vite dev server가 `/session*` 요청을 FastAPI로 프록시하고, 배포 시에는 `npm run build` 결과물(`frontend/dist`)을 FastAPI가 정적 파일로 서빙한다
- 추론 엔진은 `Engine` 인터페이스로 추상화되어 있어, 나중에 Anthropic/OpenAI API로 교체해도 파이프라인 코드는 변경하지 않는다

## 문서

- 제품 컨셉: [`docs/superpowers/specs/2026-08-18-idea-validation-agent-concept.md`](docs/superpowers/specs/2026-08-18-idea-validation-agent-concept.md)
- MVP 아키텍처 설계: [`docs/superpowers/specs/2026-08-18-idea-validation-agent-mvp-design.md`](docs/superpowers/specs/2026-08-18-idea-validation-agent-mvp-design.md)
- MVP 구현 플랜: [`docs/superpowers/plans/2026-08-18-idea-validation-agent-mvp.md`](docs/superpowers/plans/2026-08-18-idea-validation-agent-mvp.md)

## 로컬 실행

```bash
# 백엔드
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 프론트엔드 빌드 (최초 1회, 또는 프론트엔드 수정 후)
cd frontend && npm install && npm run build && cd ..

# 서버 실행 (http://127.0.0.1:8000)
.venv/bin/uvicorn app.api:app --host 127.0.0.1 --port 8000
```

프론트엔드를 개발 중일 때는 `cd frontend && npm run dev`로 별도 실행하면 (포트 5173) `/session*` 요청이 자동으로 8000번 백엔드로 프록시된다.

## 현재 상태

MVP 구현 완료 (백엔드 8단계 파이프라인 + Vite/React 프론트엔드, 리스크 우선순위화·종합판단·마크다운 저장 포함). 실제 `claude` CLI로 전체 파이프라인 E2E 검증 완료.
