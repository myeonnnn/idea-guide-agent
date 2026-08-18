# 설계: 아이디어 검증 & 로드맵 에이전트 - MVP 아키텍처

관련 문서: [2026-08-18-idea-validation-agent-concept.md](./2026-08-18-idea-validation-agent-concept.md) (제품 컨셉)

## 배경 및 결정 사항

이 문서는 컨셉 문서에서 미정으로 남아있던 기술 스택/아키텍처를 확정한다. 논의를 통해
아래 결정이 내려졌다:

- **엔진**: Anthropic API를 직접 호출하지 않고, 사용자의 로컬 터미널에 설치된
  Claude Code(`claude` CLI)를 추론 엔진으로 사용한다. API 키 발급/과금 없이 기존
  Claude Code 구독으로 동작시키는 것이 목표.
- **형태**: 웹뷰(프론트엔드) + 로컬 백엔드. 스킬(마크다운 지시문) 기반이 아니라,
  파이프라인 오케스트레이션과 자가검증 로직을 **Python 코드베이스**로 명시적으로
  구현한다. 이유: 이 프로젝트의 핵심 차별화 요소인 자가검증 루프(출처 등급화,
  신뢰도 표기)는 프롬프트 지시만으로는 신뢰성 있게 강제하기 어렵고, 코드 레벨
  검증/파싱/재시도가 필요하다.
- **범위**: 지금은 본인만 쓰는 로컬 도구로 시작. 단, 나중에 여러 사용자가 쓰는
  서비스로 확장 가능하도록 구조(특히 엔진 계층)를 깔끔하게 분리해둔다.
- **MVP 범위**: 전체 파이프라인(아이디어입력→시장조사→타겟층→가설수립→가설검증→
  MVP/MLP정의→BM가정)을 얕게 전부 구현. 자가검증 루프는 가장 기본 버전(출처 등급
  라벨링 + 출처 링크 요구)만 적용하고, 실제 재검색 교차검증은 이후 단계로 미룬다.
- **기술 스택**: 백엔드 Python/FastAPI, 프론트엔드는 빌드 스텝 없는 순수 HTML/JS.
- **엔진 교체 가능성**: 나중에 Anthropic API나 OpenAI API로 바꿀 수 있도록,
  엔진을 인터페이스로 추상화한다. 파이프라인/stage 코드는 엔진 구현 방식을 몰라야
  하며, 세션 히스토리는 CLI의 `--resume`이 아니라 **Python 쪽 세션 상태(구조화된
  단계별 산출물)를 유일한 진실 원천**으로 삼는다. 엔진 교체 시 새 `Engine` 구현체만
  추가하면 되고 파이프라인/stage 파일은 변경하지 않는다.

## 아키텍처

로컬 3계층 구조, 전부 `127.0.0.1`에서만 동작 (외부 노출 없음):

1. **프론트엔드**: 단일 페이지, 순수 HTML/JS. 대화창 + 단계 진행 표시 + 단계별
   산출물(가설표, 출처 패널) 렌더링.
2. **백엔드**: FastAPI 단일 프로세스. 세션 관리자, 파이프라인 오케스트레이터,
   엔진 래퍼로 구성.
3. **엔진**: 로컬 `claude` CLI. 백엔드가 서브프로세스로 호출.

```
[브라우저 UI] <-HTTP/SSE-> [FastAPI 백엔드] <-subprocess-> [claude CLI]
                                |
                          [세션 상태 파일]
```

## 컴포넌트

### Engine 추상화 (`engine/base.py`)
```python
class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: str

class EngineResponse(TypedDict):
    text: str
    raw: dict  # 엔진별 원본 응답 (디버깅용)

class Engine(Protocol):
    def generate(self, prompt: str, history: list[Message]) -> EngineResponse: ...
```

### ClaudeCodeCLIEngine (`engine/claude_cli.py`)
- `claude -p "<prompt>" --output-format json` 서브프로세스 실행 (`history`는
  프롬프트 조립 시 이미 반영되어 있으므로 CLI에는 넘기지 않음; `--resume`은
  선택적 성능 최적화로만 내부에서 사용 가능, 세션 진실 원천이 아님)
- stdout JSON 파싱해 텍스트 추출
- 실패 시 타입 있는 예외 발생: `EngineTimeoutError`, `EngineParseError`,
  `EngineProcessError` (CLI 미설치/미인증 포함)

### Stage 모듈 (`stages/*.py`)
6개 단계: 시장조사, 타겟층 설정, 가설 수립, 가설 검증, MVP/MLP 정의, BM 가정.
각 stage는:
- Pydantic 입력 스키마 (이전 단계들의 구조화된 산출물)
- 프롬프트 빌더 (특정 JSON 스키마로 응답하도록 요구 + 자가검증 지시 포함)
- Pydantic 출력 스키마 (파싱 실패 시 "유효한 JSON으로만 응답" 재요청 1회 재시도)

### 자가검증 모듈 (`verification/`)
- 산출물의 사실 주장(fact claim)마다 출처 등급 라벨 강제: `PRIMARY`(1차자료),
  `SECONDARY`(2차해석), `ESTIMATE`(AI추정치)
- 라벨링 결과가 스키마에 없으면 검증 실패로 처리, 재요청
- (스트레치 골, MVP 범위 아님) 동일 주장 복수 출처 재검색 교차검증

### 오케스트레이터 (`orchestrator.py`)
- 상태머신: `stage_index` + 누적된 단계별 산출물(dict)
- 순차 진행, 세션 파일에서 재개 가능

### FastAPI 라우트 (`api.py`)
- `POST /session` — 새 세션 생성, 아이디어 입력 받음
- `POST /session/{id}/message` — 사용자 입력 처리, 현재 단계 실행,
  결과 반환 및 다음 단계로 진행
- `GET /session/{id}` — 세션 전체 상태 조회 (UI 복원용)

## 데이터 흐름

1. 사용자가 아이디어 입력 → `POST /session`으로 세션 생성
2. 오케스트레이터가 stage 1(시장조사) 프롬프트 구성 (아이디어 + 자가검증 지시 포함)
3. `Engine.generate()` 호출 → JSON 파싱·Pydantic 검증 (실패 시 1회 재시도)
4. 검증된 구조화 산출물을 세션 상태에 저장
5. 프론트엔드로 반환, 다음 단계 입력 대기
6. 2~5를 6단계 반복
7. 마지막 단계 완료 후 전체 로드맵 아티팩트를 세션 상태로부터 조립해 반환

## 세션/상태 관리

로컬 파일 기반 (`./data/sessions/<id>.json`). Postgres 등 불필요 (개인용 로컬
도구이므로).

```json
{
  "id": "uuid",
  "idea": "string",
  "stage_index": 0,
  "stage_outputs": { "market_research": {...}, "target_segment": {...} },
  "created_at": "...",
  "updated_at": "..."
}
```

## 에러 처리

- `claude` CLI 미설치/미인증 → 백엔드 시작 시 헬스체크로 명확히 표시
- 서브프로세스 타임아웃 → 1회 재시도, 실패 시 UI에 재시도 버튼 노출
- JSON 파싱/스키마 검증 실패 → "반드시 유효한 JSON으로만 응답" 재요청 1회,
  그래도 실패하면 원문 + 경고 배너로 폴백 (자가검증 라벨 누락 시에도 동일 처리)
- 프로세스 크래시(non-zero exit) → stderr 로깅 후 일반 에러 메시지 표시

## 테스트

- 각 stage의 프롬프트 빌더·출력 스키마 파싱 단위테스트 (`Engine`을 목킹, 실제
  CLI 호출 없이 진행)
- 오케스트레이터 상태 전이 단위테스트 (단계 진행, 재개, 저장/로드)
- 자가검증 모듈: 라벨 누락/불완전 케이스에 대한 검증 실패 처리 단위테스트
- E2E는 실제 `claude` 인증이 필요하므로 수동 실행으로만 (CI에 포함하지 않음)

## 다음 단계

이 스펙을 기반으로 구현 플랜(writing-plans)을 작성한다. 첫 구현 순서는:
1. `Engine` 인터페이스 + `ClaudeCodeCLIEngine` 구현 + 단위테스트
2. 세션 상태 저장/로드
3. Stage 모듈 1개(시장조사)로 파이프라인 배관 검증
4. 나머지 5개 stage 순차 추가
5. FastAPI 라우트 + 최소 프론트엔드 연결
