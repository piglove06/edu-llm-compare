# edu-llm-compare

Private LLM 과정 실습 프로젝트 — 로컬 LLM 2개(granite-4.1-3b, exaone3.5:7.8b) + Cloud API 1개를 문서 분석 태스크로 비교하여 최종 모델 1개를 선정합니다.

---

## STEP 0. 모델 설치 및 실행

### 0.1 exaone3.5:7.8b
- Hugging Face: https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct

```powershell
ollama pull exaone3.5:7.8b
ollama run exaone3.5:7.8b
ollama stop exaone3.5:7.8b
```

### 0.2. granite-4.1-3b
- Hugging Face: https://huggingface.co/ibm-granite/granite-4.1-3b

```powershell
ollama pull granite4.1:3b
ollama run granite4.1:3b
ollama stop granite4.1:3b
```


### 0.3. 설치 확인 (`ollama list`)

| NAME | ID | SIZE | MODIFIED |
|---|---|---|---|
| exaone3.5:7.8b | c7c4e3d1ca22 | 4.8 GB | About an hour ago |
| qwen3:4b-instruct-2507-q4_K_M | 0edcdef34593 | 2.5 GB | 4 days ago |
| granite4.1:3b  | 6fd349357287 | 2.1 GB | 2 minutes ago |

---

## STEP 1. 문제 정의

**문서분석모델**

- **Target**: 
  - Private LLM수업을 듣는 학생
- **사용목적**:
  - 현재 Private LLM수업 시 내용분석 및 어려운 내용을 쉽게 설명받고 싶음.
  - 수업자료 예습 및 복습을 위한 수업자료 내용을 쉽게 설명, 요약, 전체적인 흐름 요청
  - GitHub & Hugging Face 내용분석 및 논문내용을 쉽게 분석하기 위함.
  - 핸드폰에서도 쉽게 공부할 수 있어야하며, 피시에서 풀었을떄의 진행상황이 모바일과 공유되어야함.

- **사용시점**:
  - 수업시작 전 및 쉬는시간에 다음수업 예습 시 사용
  - 수업이 끝난 이후 복습
  - 수업이 끝난 이후 수업과 관련된 GitHub, Hugging Face의 내용분석
  - 언제 어디서든 내가 공부하고 싶을 때 할 수 있어야함.
  
- **발전가능성**:
  - 각 LLM이 내 수업질문과 수업자료를 통해 내가 얼마나 해당과목을 이해하고 있는지 확인가능
  - LLM이 각 파트별 사용자의 학습여부를 수치화하여 저장 후, 난이도에 맞는 문제출제 및 심화과정 추가학습

- **사용환경**:
  - 수업용 노트북
  - GPU: NVIDIA GeForce RTX 5060 Laptop GPU (8GB VRAM)
  - CPU: Intel(R) Core(TM) Ultra 9 275HX (2.70 GHz)
  - OS: Windows 11 Pro 64비트
  - RAM: 32G DDR5 
  - 저장장치: 1TB (954 GB 중 174 GB 사용됨)

---

## STEP 2. 모델 요구사항 정의

### 2.1 필수 통과 조건

| 조건 | 확인 방법 | granite4.1:3b | EXAONE3.5:7.8B |
|---|---|---|---|
| RTX 5060(8GB VRAM) 노트북에서 실행 가능 | `ollama run`으로 정상 구동 확인 | ✅ (2.2GB) | ✅ (4.8GB) |
| 연구/개인 학습 목적 사용 가능한 라이선스 | 라이선스 확인 | ✅ Apache 2.0 | ✅ EXAONE 1.1-NC (비상업 연구/학습 목적 한정 — 본 프로젝트 용도 문제없음) |
| md/PDF 문서 길이를 수용하는 Context Length | Model Card 확인 | ✅ 131,072 토큰 | ✅ 32,768 토큰 |
| 한국어 질문 → 한국어 답변 기본 동작 | 프롬프트 입력하여 확인 | ✅ 한국어 응답 확인됨 | ✅ 한국어 응답 확인됨 |
| Instruct/Chat 태스크 지원 | Model Card 확인 | ✅ | ✅ |


### 2.2 선호 우선순위

1. **할루시네이션이 없는 결과물** — 원문에 없는 내용을 지어내지 않고, 모르면 모른다고 물어보는지 확인
2. **사용자가 판단하에 원하는 결과물** — 지시(요약/설명/지정 항목 질의)를 얼마나 정확히 이행하는지 여부
3. **가독성이 좋은 결과물** — 질문주제에 대한 답변인지 여부, 핵심이외에 부가설명이 최대한 없는 결과물을 원함
4. **속도** — 응답 시간 및 VRAM 사용량(우선순위 낮음)

---

## STEP 3. 후보 모델 탐색

### 3-1. EXAONE-3.5-7.8B-Instruct

| 항목 | 내용 |
|---|---|
| Model Name | EXAONE-3.5-7.8B-Instruct |
| Parameter Size | 7.8B (Ollama 실측: `parameters 7.8B`, embedding length 4096) |
| License | EXAONE AI Model License Agreement 1.1 - NC (비상업 연구/학습 목적 한정) |
| Context Length (Model Card 최대) | 32,768 토큰 |
| Context Length (실험 설정값) | (실험 시 num_ctx 기재 예정) |
| Architecture | EXAONE (Transformer, GQA 32 Q-heads / 8 KV-heads) |
| Language | 영어, 한국어 (bilingual) |
| Model Card | https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct |
| License 원문 | https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct/blob/main/LICENSE |
| Quantization 지원 여부 | 지원 (AWQ, GGUF 다수 양자화 버전 공식 제공) |
| 실행 Ollama 태그 | `exaone3.5:7.8b` (ID: `c7c4e3d1ca22`) |
| 원본 모델과의 대응 관계 | LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct → Q4_K_M 양자화 GGUF 변환판 |
| 다운로드 파일 크기 | 4.8GB |
| 시스템 RAM 사용량 | (실험 시 측정 예정) |
| VRAM 사용량 | (실험 시 `ollama ps`의 size_vram으로 측정 예정) |
| **최종 선택 이유** | 1. 국내모델을 테스트하고싶었음. 2. Parameter Size가 10B미만 모델 선택. 3. 한국어 특화 벤치마크에서 동급 크기 모델 대비 우수한 성능  |

---

### 3-2. granite-4.1-3b

| 항목 | 내용 |
|---|---|
| Model Name | granite-4.1-3b |
| Parameter Size | 3.4B (Ollama 실측) |
| License | Apache 2.0 |
| Context Length (Model Card 최대) | Ollama 소개 문구 기준 "학습 시 512K까지 확장" 언급 있으나, `ollama show`로 실측 시 131,072(128K) 토큰이 실제 서빙 값 |
| Context Length (실험 설정값) | (실험 시 num_ctx 기재 예정) |
| Architecture | Granite (Dense decoder-only Transformer, GQA, RoPE, MLP with SwiGLU, RMSNorm) |
| Language | 한국어, 영어 등 12개 언어 공식 지원 |
| Model Card | https://huggingface.co/ibm-granite/granite-4.1-3b |
| License 원문 | Apache 2.0 표준 라이선스 |
| Quantization 지원 여부 | 지원 (GGUF 다수 존재, Ollama 기본 배포가 Q4_K_M) |
| 실행 Ollama 태그 | `granite4.1:3b` (ID: 실행 후 `ollama list`로 확인) |
| 원본 모델과의 대응 관계 | ibm-granite/granite-4.1-3b → Q4_K_M 양자화 GGUF 버전 (`ollama show`로 실측 확인) |
| 다운로드 파일 크기 | 2.2GB |
| 시스템 RAM 사용량 | (실험 시 측정 예정) |
| VRAM 사용량 | (실험 시 `ollama ps`의 size_vram으로 측정 예정) |
| **최종 선택 이유** | 1. IBM모델 테스트하고싶었음. 2. Parameter Size가 작은 모델로 비교해보고싶어 선택 3. Model Card에 한국어가 공식 지원 언어로 명시되어 있어 선택.  |

---

### 3-3. Mistral-7B-Instruct-v0.3

| 항목 | 내용 |
|---|---|
| Model Name | Mistral-7B-Instruct-v0.3 |
| Parameter Size | 7B |
| License | Apache 2.0 |
| Context Length (Model Card 최대) | **Model Card에 설명 없음**  |
| Context Length (실험 설정값) | (실험 시 num_ctx 기재 예정) |
| Architecture | Mistral (Sliding Window Attention, GQA), Function calling 지원 |
| Language | **Model Card에 설명 없음** |
| Model Card | https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3 |
| License 원문 | Apache 2.0 표준 라이선스 |
| Quantization 지원 여부 | 지원 |
| 실행 Ollama 태그 | `mistral` |
| 원본 모델과의 대응 관계 | 최종 후보에서 제외되어 상세 검증 생략 (미설치) |
| 다운로드 파일 크기 | 4.4GB |
| 시스템 RAM 사용량 | (미측정) |
| VRAM 사용량 | (미측정) |
| **최종 선택 제외 이유** | 1. 한국어 공식지원 설명없음.  2. Model Card에 등록된 정보가, 다른모델에 비해 부실함(지원 언어 명시, Context Length 등등)  |

---

### 3-4. Yi-1.5-6B-Chat

| 항목 | 내용 |
|---|---|
| Model Name | Yi-1.5-6B-Chat |
| Parameter Size | 6B |
| License | Apache 2.0 |
| Context Length (Model Card 최대) | **4,096 토큰**  |
| Context Length (실험 설정값) | (실험 시 num_ctx 기재 예정) |
| Architecture | Yi (Llama 구조 채택, 단 Llama 가중치 파생 아님 — 독자 학습) |
| Language | 영어/중국어 bilingual — **한국어 공식 지원 언급 없음** |
| Model Card | https://huggingface.co/01-ai/Yi-1.5-6B-Chat |
| License 원문 | Apache 2.0 표준 라이선스 |
| Quantization 지원 여부 | 지원  |
| 실행 Ollama 태그 | `yi:6b-chat-v1.5-q5_K_M` |
| 원본 모델과의 대응 관계 | 최종 후보에서 제외되어 상세 검증 생략 (미설치) |
| 다운로드 파일 크기 | 4.3GB |
| 시스템 RAM 사용량 | (미측정) |
| VRAM 사용량 | (미측정) |
| **최종 선택 제외 이유** | 1. 한국어 공식지원 설명없음.  2. 최근 해당모델 업데이트이력없음  |

---

### 3-5. Meta-Llama-3-8B-Instruct

| 항목 | 내용 |
|---|---|
| Model Name | Meta-Llama-3-8B-Instruct |
| Parameter Size | 8B |
| License | Meta Llama 3 Community License (커스텀 라이선스, 완전 오픈소스 아님 — 월간 활성 사용자 7억 명 초과 시 별도 계약 필요) |
| Context Length (Model Card 최대) | 8,192 토큰 |
| Context Length (실험 설정값) | (실험 시 num_ctx 기재 예정) |
| Architecture | Llama 3 (Auto-regressive Transformer, GQA), SFT+RLHF로 정렬 |
| Language | 영어 중심 — **한국어 공식 지원 언급 없음** |
| Model Card | https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct |
| License 원문 | Meta Llama 3 Community License (모델 카드 내 명시, 접근 시 별도 동의 절차 필요) |
| Quantization 지원 여부 | 지원 (GGUF 다수 존재) |
| 실행 Ollama 태그 | `llama3:8b` (공식 Ollama 라이브러리, 미설치 — 설치 시 `ollama show`로 재확인 필요) |
| 원본 모델과의 대응 관계 | 최종 후보에서 제외되어 상세 검증 생략 (미설치) |
| 다운로드 파일 크기 | (미설치 — 통상 8B급 Q4_K_M 기준 약 4.7GB대로 추정) |
| 시스템 RAM 사용량 | (미측정) |
| VRAM 사용량 | (미측정) |
| **최종 선택 제외 이유** | 1. 공식 지원 언어에 한국어가 명시되어 있지 않음 (Llama 3.1부터 다국어 지원 명시 시작). 2. Context Length(8,192)가 최종 후보(EXAONE 32K, granite4.1 131K) 대비 짧아 수업 PDF 등 긴 문서 처리에 불리. |

---

### 3-6. Qwen3-4B-Instruct-2507

| 항목 | 내용 |
|---|---|
| Model Name | Qwen3-4B-Instruct-2507 |
| Parameter Size | 4B (HF 표기), 실제 config 기준 약 4.02B |
| License | Apache 2.0 |
| Context Length (Model Card 최대) | 262,144 토큰 |
| Context Length (실험 설정값) | (실험 시 num_ctx 기재 예정) |
| Architecture | Qwen3 Dense, non-thinking instruct 전용 (thinking 블록 생성 안 함) |
| Language | 다국어 (29개 이상 언어, long-tail 다국어 지식 강화) |
| Benchmark | Model Card 기준 "Qwen3-4B가 Qwen2.5-72B-Instruct급 성능에 근접" 주장 (세부 수치는 기술 리포트 별도 확인 필요) |
| Model Card | https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507 |
| License 원문 | Apache 2.0 표준 라이선스 (Model Card 내 라이선스 섹션) |
| Quantization 지원 여부 | 지원 — 현재 실행 중인 버전이 Q4_K_M 양자화판 |
| 실행 Ollama 태그 | `qwen3:4b-instruct-2507-q4_K_M` (ID: `0edcdef34593`) |
| 원본 모델과의 대응 관계 | 최종 후보에서 제외되어 상세 검증 생략 (미설치) |
| 다운로드 파일 크기 | 2.5GB |
| 시스템 RAM 사용량 | (실험 시 측정 예정) |
| VRAM 사용량 | (실험 시 측정 예정) |
| **최종 선택 제외 이유** | 1. qwen 3.8 7b모델을 예전에 사용해본결과 원하는대로 제대로 동작하지 않아 제외 2. 사용하지 않은 모델 위주로 테스트하고싶어 granite4.1로 대체.  |

---

## STEP 4. 모델 실행 환경 확인과 Python 연결
1. 모델 실행환경을 Log에 출력하며, JSONL포맷으로 Log File 저장. (기존에 회사에서 사용하던 방식은 log4net, log4j 등)

---

## STEP 5 ~ 7. 평가 질문 List 생성 및 성능 측정

3개 모델에 10개 질문을 하고, 대답결과에 따라 점수를 매김.
cloud모델도 문제개수를 5개로 줄일 이유가 없다고 생각되어, 기존에 선택한 10문제 그대로 평가.

### 5.1 질문 구성 (4가지 사례 유형)

발제문이 제시한 3가지 사례에, 실제 사전 테스트에서 발견한 **"비정상 사례"**를 추가로 정의합니다.

- **정상 사례**: 문서 원문이 정확히 주어졌을 때 요약/설명/사실 추출을 요청
- **경계 사례**: 조건이 애매하거나 판단이 어려운 경우 (형식 지시, 비교 추론 등)
- **정보부족 사례**: 문서에 없는 정보를 요청 — "모른다"고 인정하는지 확인
- **비정상 사례 (신규 추가)**: 모델이 접근할 수 없는 자료(URL 등)를 "참고했다는 전제"로 질문해, 실제로 접근하지 않았음에도 접근한 것처럼 답변을 지어내는지(hallucination) 확인하는 사례

> **비정상 사례를 추가한 이유**: 사전 테스트에서 "URL을 참고해서 답해달라"는 질문에 두 모델 모두 실제로 URL에 접근하지 않았음에도 마치 확인한 것처럼 답변하는 현상을 관찰했습니다. 로컬 LLM은 인터넷 접근 권한을 주지 않았는데, url을 확인하여 답을 알려준 것처럼 대답하는 경우가 발생하여 추가.

### 5.2 질문에 사용되는 문서

| 문서 ID | 파일명 | 내용 |
|---|---|---|
| DOC-A | (readfiles 폴더 내 지정) | Qwen3.8-Flash-Next Model의 README.md file |
| DOC-B | (readfiles 폴더 내 지정) | 수업자료 PDF(10장 1강 Timeout/Rate Limit/Retry/Fallback) |

### 5.3 품질 채점 기준 (STEP2 선호순위 반영)

1. **할루시네이션 없음** (0~4점): 원문/접근 불가 자료에 대해 지어낸 답을 하지 않는가 — Q1이 이 기준의 핵심 검증 질문
2. **지시 이행도** (0~4점): 요청한 형식/분량을 지켰는가
3. **결과값에 대한 사용자 만족도(주관적)** (0~2): 원하는 내용이 잘 출력되었는지, 출력값이 가독성이 좋은지, 설명을 얼마나 잘하는지 등등


### 5.4.1 프롬프트 튜닝 전 고정 질문 세트 10개

| ID | 사례 유형 | 입력 자료 | 질문 | 기대 결과 / 확인할 항목 |
|---|---|---|---|---|
| Q1 | 비정상 | 원문 미제공, URL만 제시 | (기존 유지) | (기존 유지) |
| Q2 | 정상(자유요약) | DOC-A 원문 제공 | "이 문서 내용을 초보자도 이해하기 쉽게 3~4문장으로 요약해 주세요." | Qwen3.8-Flash-Next의 핵심 특징(하이브리드 어텐션, MoE 구조 등) 언급 여부 |
| Q3 | 정상(사실추출) | DOC-A 원문 제공 | "이 모델의 전체 파라미터 수와 실제 활성화되는 파라미터 수는 각각 몇 개인가요?" | 정답: 125B(전체) / 6B(활성화) |
| Q4 | 정상(사실추출) | DOC-A 원문 제공 | "이 모델의 기본 Context Length와 확장 가능한 최대 Context Length는 얼마인가요?" | 정답: 262,144(기본) / 1,000,000(확장 시) |
| Q5 | 경계(지시이행) | DOC-A 원문 제공 | "이 모델의 라이선스를 정확히 한 단어로만 답해 주세요." | license_name: qwen-community-1.0 — "Apache" 등으로 잘못 지어내지 않는지 |
| Q6 | 정보부족 | DOC-A 원문 제공 | "이 모델의 정확한 출시일(연/월/일)이 언제인가요?" | 원문에 정확한 날짜 없음(월/년만 있음) → "명시 안 됨"이라 답하는지 |
| Q7 | 정상(자유요약) | DOC-B 원문 제공 | "이 문서 내용을 초보자도 이해하기 쉽게 3~4문장으로 요약해 주세요." | API 재시도/백오프/fallback 핵심 개념 언급 여부 |
| Q8 | 정상(사실추출) | DOC-B 원문 제공 | "OpenAI Python SDK는 어떤 오류들을 기본적으로 몇 번 재시도하나요?" | 정답: 연결 오류/408/409/429/5xx, 기본 2번 |
| Q9 | 경계(비교종합) | DOC-A + DOC-B 동시 제공 | "두 문서는 각각 어떤 주제를 다루고 있나요? 공통점이 있다면 설명해 주세요." | DOC-A(모델 아키텍처) vs DOC-B(API 안정성)를 정확히 구분하는지 — 성격이 전혀 다른 두 문서를 섞어서 잘못된 답을 지어내지 않는지 확인 |
| Q10 | 경계(지시이행+형식) | DOC-B 원문 제공 | "재시도가 불가능한 대표적인 오류 3가지를 마크다운 표로 정리해 주세요." | 정답: 잘못된 API key, 400 Bad Request, permission denied 등 — 표 형식 준수 여부 |


### 5.4.2 프롬프트 튜닝 후 고정 질문 세트 10개

텍스트가 길어 생략.
log_04_document_qa.jsonl file 참고


### 5.4.3 프롬프트 튜닝 전 품질 채점 결과

| ID | 모델 | 할루시네이션 (0~4) | 지시이행 (0~4) | 만족도 (0~2) | Total (0~10) | 사유 |
|---|---|:---:|:---:|:---:|:---:|---|
| Q1 | exaone3.5:7.8b | 0 | 4 | 0 | **4** | url접근권한 주지 않았는데, 기존학습된 데이터로 응답. |
| Q1 | granite4.1:3b | 0 | 4 | 0 | **4** | url접근권한 주지 않았는데, 기존학습된 데이터로 응답 + 쓸데없이 답변이 너무 길고 num_predict설정범위가 넘어 텍스트가 잘림 |
| Q1 | gpt-5.6-luna | 0 | 4 | 0 | **4** | url접근권한 주지 않았는데, 기존학습된 데이터로 응답 + 추가로 url을 끝에 -ver2를 붙여 잘못된url를 주었는데도 있는것처럼 대답하였음. 할루시네이션이 없을거라 생각했는데 로컬모델과 동일결과가 흥미로웠음. |
| Q2 | exaone3.5:7.8b | 4 | 2 | 2 | **8** | 작은모델치고 특징을 잘 뽑아내었지만, 3~4문장에 비해 답변길이가 길었음 |
| Q2 | granite4.1:3b | 4 | 2 | 1 | **7** | 작은모델치고 특징을 잘 뽑아내었고 초보자가 보기에도 쉽게 대답하였지만, 특징을 잘 추출하지 못함. |
| Q2 | gpt-5.6-luna | 4 | 4 | 2 | **10** | 참고 문서파일에 있는 Highlights의 중요내용을 전부 표시하 |
| Q3 | exaone3.5:7.8b | 4 | 0 | 0 | **4** | 할루시네이션은 없었지만, 파라메터수가 나와있는데 찾지못하였고, 쓸데없는 답변이 너무 김. |
| Q3 | granite4.1:3b | 0 | 0 | 0 | **0** | 전체파라메터개수가 1,024,000,000 정도라고 할루시네이션이 있었으며, 전체적으로 원하는 답변이 없음 |
| Q3 | gpt-5.6-luna | 4 | 4 | 1 | **9** | 125B, 6B를 정확히 지정하였지만, CHATGPT특징인 불필요한 추가답변이 거슬렸음. |
| Q4 | exaone3.5:7.8b | 0 | 2 | 0 | **2** | 기본 4096, 확장 262144"로 완전히 틀림 |
| Q4 | granite4.1:3b | 0 | 3 | 1 | **4** | 128,000 ~ 262,144 tokens로 틀렸지만 exaone3.5:7.8b에 비해 정답에 근접 |
| Q4 | gpt-5.6-luna | 4 | 4 | 2 | **10** | 기본토큰개수와 확장토큰개수와 추가설명까지 원하는 대로 결과가 나옴 |
| Q5 | exaone3.5:7.8b | 0 | 0 | 0 | **0** | Apache-2.0으로 틀리게 대답 |
| Q5 | granite4.1:3b | 0 | 0 | 0 | **0** | MIT로 틀리게 대답 |
| Q5 | gpt-5.6-luna | 4 | 4 | 2 | **10** | 정답과 질문대로 짧게 정답만 잘 대답하여 만족 |
| Q6 | exaone3.5:7.8b | 4 | 4 | 1 | **9** | 해당문서에 정의되어 있지 않다고 정확히 대답하였으나, 부가설명이 너무 길었음. |
| Q6 | granite4.1:3b | 2 | 4 | 2 | **8** | 해당문서에는 정의되어 있지 않지만, 학습에 데이터가 들어있었는지 정답을 맞힘. 추후 시간여유가 되면 RAG를 참고하여 답변하였는지, 사전학습데이터로 응답하였는지, 찍었는데 맞았는지 분석필요. |
| Q6 | gpt-5.6-luna | 4 | 4 | 2 | **10** | 해당문서에 정의되어 있지 않다고 정확히 대답하였으며, 기존학습된 데이터로 날짜도 정확히 맞추었음. |
| Q7 | exaone3.5:7.8b | 4 | 4 | 2 | **10** | 대답품질에 만족 |
| Q7 | granite4.1:3b | 4 | 1 | 0 | **5** | 3~4문장이라고 하였는데 한문장 정도로 짧게 응답하였고, 답변끝이 잘림. |
| Q7 | gpt-5.6-luna | 4 | 4 | 1 | **9** | 대답품질에 만족하였지만 좀 더 짧고 쉽게 대답을 원했는데 아쉬움. 문장보단 글자수를 맞추는게 해당상황에서 더 도움된다는 결과를 얻음. |
| Q8 | exaone3.5:7.8b | 0 | 3 | 0 | **3** | 재시도 대상 오류(연결오류/429/5xx)는 정확하였지만, 재시도횟수는 명시되어있지만 없다고 답변하였으며, OpenAI SDK에 없는 메소드명을 알려주었음. |
| Q8 | granite4.1:3b | 3 | 4 | 2 | **9** | 기본2회였지만 일반적으로 3회로 대답하였음. 하지만 정답과 차이가 크지 않으며, 전반적인 응답품질이 괜찮아 높은점수를 줌 |
| Q8 | gpt-5.6-luna | 4 | 4 | 2 | **10** | 대답품질에 만족 |
| Q9 | exaone3.5:7.8b | 0 | 1 | 0 | **1** | DOC-A에 대한 내용이 없으며, 문서두개 비교내용이 없고 두개를 비교한 것처럼 설명함. |
| Q9 | granite4.1:3b | 0 | 1 | 0 | **1** | DOC-A내용이 없으며 exaone3.5와 비슷하게 안좋은 응답 |
| Q9 | gpt-5.6-luna | 4 | 4 | 2 | **10** | DOC-A, DOC-B 문서구분을 정확히하였고, 문서의 특징과 전혀 연관없다.|
| Q10 | granite4.1:3b | 4 | 2 | 2 | **8** | 전체적으로 만족스러운 답변 |
| Q10 | gpt-5.6-luna | 4 | 4 | 2 | **10** | 대답품질에 만족|


### 5.4.4 프롬프트 튜닝 전 결과 요약

| 모델 | 할루시네이션 | 지시이행 | 만족도 | 총점 | 
| --- | :---: | :---: | :---: | :---: |
| exaone3.5:7.8b | 20/40 | 23/40 | 7/20 | **50/100** | 
| granite4.1:3b | 17/40 | 21/40 | 8/20 | **46/100** | 
| gpt-5.6-luna | 36/40 | 40/40 | 16/20 | **92/100** | 


### 5.4.5 프롬프트 튜닝 후 품질 채점 결과

| ID | 모델 | 할루시네이션 (0~4) | 지시이행 (0~4) | 만족도 (0~2) | Total (0~10) | 사유 |
| --- | --- | :---: | :---: | :---: | :---: | --- |
| Q1 | exaone3.5:7.8b | 4 | 4 | 2 | **10** | URL 내용을 확인할 수 없다고 명확하게 답변 |
| Q1 | granite4.1:3b | 4 | 4 | 2 | **10** | URL 내용을 확인할 수 없다고 명확하게 답변 |
| Q1 | gpt-5.6-luna | 4 | 4 | 2 | **10** | URL 내용을 확인할 수 없다고 명확하게 답변 |
| Q2 | exaone3.5:7.8b | 4 | 2 | 1 | **7** | 3문장 이내로 잘 대답하였지만, 파일에 명시된 중요항목을 잘 캐치하지못함. |
| Q2 | granite4.1:3b | 2 | 2 | 1 | **5** | 3문장 이내로 잘 대답하였지만, 파일에 명시된 중요항목을 잘 캐치하지못하였고, `크로프(ROPE)`라는 기술을 설명하였지만 RoPE 포지션 기술은 크로프라고 발음하지 않으며 긴 문서를 빠르게 처리하는 기능이라고 답변하기엔 모호하지만 틀린 답변에 더 가까움|
| Q2 | gpt-5.6-luna | 4 | 3 | 2 | **9** | 3문장 이내로 잘 대답하였지만, 1차 실행에서는 MoE 구조를 콕 찝어서 언급하지 않았음. |
| Q3 | exaone3.5:7.8b | 0 | 0 | 1 | **1** | 임의의 수치를 지어내지는 않았지만, 문서에 있는 125B와 6B를 찾지 못하고 한 줄 형식도 지키지 않았음. 질문 프롬프트에 '전체'라는 단어와, DOC-A파일에 plus라는 단어가 LLM이 판단할 때 오류를 낸 것으로 추측.(모티프 LLM 추론로그로 추측) |
| Q3 | granite4.1:3b | 0 | 0 | 1 | **1** | 정답과 무관한 1,024,000,000을 전체·활성 파라미터로 대답함. 질문 프롬프트에 '전체'라는 단어와, DOC-A파일에 plus라는 단어가 LLM이 판단할 때 오류를 낸 것으로 추측.(모티프 LLM 추론로그로 추측) |
| Q3 | gpt-5.6-luna | 4 | 4 | 2 | **10** | 전체 125B와 활성 6B를 정확히 찾았으며, 요청한 한 줄 형식도 지켰다. |
| Q4 | exaone3.5:7.8b | 0 | 4 | 1| **5** | `2048 / 262144`로 답해 기본값과 확장값 모두 틀림  |
| Q4 | granite4.1:3b | 4 | 4 | 2 | **10** | 대답품질에 만족 |
| Q4 | gpt-5.6-luna | 4 | 4 | 2 | **10** | 대답품질에 만족 |
| Q5 | exaone3.5:7.8b | 0 | 0 | 0 | **0** | 정답인 `qwen-community-1.0`이 아니라 `MIT License`를 제시했다. |
| Q5 | granite4.1:3b | 0 | 0 | 0 | **0** | 라이선스를 `CC BY 4.0`으로 잘못 제시했다. |
| Q5 | gpt-5.6-luna | 4 | 4 | 2 | **10** | 대답품질에 만족  |
| Q6 | exaone3.5:7.8b | 4 | 4 | 2 | **10** | 정확한 날짜가 문서에 없다고 출력.|
| Q6 | granite4.1:3b | 4 | 4 | 2 | **10** | 정확한 날짜가 문서에 없다고 출력.|
| Q6 | gpt-5.6-luna | 4 | 4 | 2 | **10** | 정확한 날짜가 문서에 없다고 출력. |
| Q7 | exaone3.5:7.8b | 4 | 4 | 2 | **10** | 대답품질에 만족. |
| Q7 | granite4.1:3b | 4 | 2 | 1 | **7** | 핵심 개념은 언급했지만 5문장으로 요청사항을 지키지 못했고 `jitter`를 `잡티`, `idempotency`를 `원자성`으로 잘못 번역하여 알려줌. |
| Q7 | gpt-5.6-luna | 4 | 4 | 2 | **10** | 대답품질에 만족. |
| Q8 | exaone3.5:7.8b | 0 | 3 | 1 | **4** | 재시도 대상 오류는 맞췄지만, 기본 재시도 횟수 0회로 틀린 답변을 함. |
| Q8 | granite4.1:3b | 0 | 3 | 1 | **4** | 연결 오류 누락, 기본 횟수도 2회가 아닌 3회로 틀린 답변을 함. |
| Q8 | gpt-5.6-luna | 4 | 4 | 2 | **10** | 대답품질에 만족. |
| Q9 | exaone3.5:7.8b | 0 | 1 | 1 | **2** | DOC-A의 주제를 모두 잘못 구분했다. 잘못된 대답을 사실처럼 대답. |
| Q9 | granite4.1:3b | 0 | 1 |1 | **2** | DOC-A와 DOC-B의 주제를 모두 잘못 구분했다. 잘못된 대답을 사실처럼 대답. |
| Q9 | gpt-5.6-luna | 4 | 4 | 2 | **10** | 대답품질에 만족. |
| Q10 | exaone3.5:7.8b | 4 | 4 | 2 | **10** | 대답품질에 만족. |
| Q10 | granite4.1:3b | 4 | 2 | 1 | **7** | 오류 3개와 표 내용은 좋았지만, 표 앞뒤에 설명을 추가하지 말라는 지시를 지키지 않음. |
| Q10 | gpt-5.6-luna | 4 | 4 | 2 | **10** | 대답품질에 만족. |


### 5.4.6 프롬프트 튜닝 후 결과 요약

| 모델 | 할루시네이션 | 지시이행 | 만족도 | 총점 | 
| --- | :---: | :---: | :---: | :---: | 
| exaone3.5:7.8b | 20/40 | 26/40 | 13/20 | **59/100** |
| granite4.1:3b | 22/40 | 22/40 | 12/20 | **56/100** | 
| gpt-5.6-luna | 40/40 | 39/40 | 20/20 | **99/100** |


### 5.4.7 프롬프트 튜닝 전 후 결과 비교

| 모델 | 튜닝 전 점수 | 튜닝 후 점수 | 점수 변화 | 결과 분석 |
|---|:---:|:---:|:---:|---|
| exaone3.5:7.8b | 50점 | 59점 | **+9점** | 테스트결과 8b랑 3b의 한글최적화 이외의 유의미한 성능차이를 느끼지 못하였음. |
| granite4.1:3b | 46점 | 56점 | **+10점** | `크로프(ROPE)`, `잡티(jitter)` 등 전문용어를 한글로 어색하게 번역하거나, 단어번역 결과가 틀린항목이 몇개 보였음. 한글모델에 비해 한글최적화가 덜된게 가장 큰 차이.
| gpt-5.6-luna | 92점 | 99점 | **+7점** | 당연히 더 성능이 좋은건 예상했지만, 의외로 프롬프트 튜닝 전 url접근권한이 없는데 보고 대답한 것 같은 답변이 의외였음. |
문제3번의경우 모델의 파라메터를 찾는 간단한 문제라 판단하였는데 로컬모델 둘 다 틀렸으며,
문제3번 질문 프롬프트에 '전체'라는 단어와,  md파일에 plus라는 단어가 LLM이 판단할 때 오류를 낸 것으로 추측(모티스 모델로 추가테스트시 Log로 확인).

---



## 프로젝트 주요 산출물

1. GitHub Repository
2. Model Comparison Table
3. Model Test / Benchmark 결과
4. Local LLM vs Cloud API 비교
5. 최종 Model Selection Report

---

## 프로젝트 요구사항 충족도 평가표

| 요구사항 | 수행할 작업 (STEP) | 완료 기준/확인할 증빙 |
|---|---|---|
| 1. 문제/요구사항 정의 | STEP 1~2 | 사용 사례를 정의하고, 필수 통과 조건과 선호 우선순위를 실험 전에 정합니다. 사용자/태스크/제약조건과 선정 기준이 정리되어 있고, 조건별 확인 방법과 우선순위를 설명할 수 있습니다. |
| 2. 후보 모델 조사 | STEP 3 | 서로 다른 로컬 후보 2개의 특성과 실행 가능 조건을 조사합니다. Model Card/License 출처, 모델 크기/Context/양자화, 실제 모델 태그/식별값과 후보 선정 이유가 기록되어 있습니다. |
| 3. 실행 환경/기록 확인 | STEP 4 | 두 후보를 Python으로 호출하고 결과 한 건을 파일에 저장한 뒤 다시 확인합니다. 모델별 기본 응답, Python/Ollama/주요 패키지/장비/설정 정보와 저장된 원본 기록을 확인할 수 있습니다. |
| 4. 평가 질문/기준 확정 | STEP 5 | 질문 10개와 기대 결과/품질 채점 기준을 정하고, Cloud용 5문항을 미리 선정합니다. 질문 ID/입력 자료/기대 결과 또는 확인 항목이 있으며, 정상/경계/정보 부족 사례와 동일 입력/설정 적용 기준이 정리되어 있습니다. |
| 5. 로컬 비교 실험 | STEP 6 | 로컬 모델 2개 × 질문 10개 × 각 2회를 실행하고, 모델당 워밍업 1회와 구분합니다. 본 실험 40회의 응답/설정/성공/오류 기록과 전체 응답 시간/로딩 시간/출력 토큰 수/생성 속도/VRAM 기록을 확인할 수 있습니다. |
| 6. 품질 평가/해석 | STEP 5~6 | 원본 응답을 동일 기준으로 채점하고 점수 근거와 대표 성공/실패 사례를 분석합니다. 점수의 근거가 응답 부분과 연결되고, 평균 및 집계 응답 수를 원본 기록에서 확인할 수 있습니다. |
| 7. Local–Cloud 비교 | STEP 7 | Cloud 모델 1개에 공통 질문 5개를 각 1회 적용하고 로컬의 동일 문항 결과와 비교합니다. Cloud 응답/상태/시간/토큰 사용량/비용과 품질 평가가 있습니다. |
| 8. 최종 모델 선정/발표 | STEP 8 | 두 로컬 후보의 필수 조건 충족 여부를 확인하고 우선순위에 따라 후보 1개를 선정합니다. 선택/탈락 이유가 요구사항과 실험 근거에 연결됩니다. |
| 9. 제출/재실행 확인 | 산출물 전체 | 저장소 하나에 코드/환경/질문/원본 기록/비교표/선정 근거를 모읍니다. README에서 실행 방법과 자료 위치를 확인할 수 있습니다. |

---

## STEP 8. 최종 모델 선정과 발표
최종 모델 : luna
선정사유 : 
1.1 언제 어디서든 모바일환경에서 접속 가능하여아하며, pc와 모바일에서 사용시 공부한 이력이 동기화 되어야함.
1.2 로컬버전의 경우 해당기능 사용시 추가로 개발해야할 사항이 너무 많음(서버, 클라이언트, db 등등)
2. 현재 클로드에 비슷한 기능을 만들어서 사용중이므로, 무조건 선택이 필요하다면 luna 선택.

로컬모델 미선정사유
1. 모바일접속 + pc와 모바일버전 학습진행상황 저장 및 동기화시 너무 많은 개발이 소요됨.
2. RAG를 연동하였어도, 할루시네이션이 생각보다 심함.
3. 다만 로컬모델의 기능을 최대한 끌어올리는 LLM Ops공부에는 도움이 많이 될 것으로 생각됨.



## 참고 URL

1. [edu-llm-compare (프로젝트 저장소)](https://github.com/piglove06/edu-llm-compare)


---

## 기타 (실행 명령어 모음)

### 1. PowerShell - 프로젝트 폴더 이동

```powershell
cd "C:\Users\piglo\OneDrive\Desktop\KANT LLM\페이지 PDF\98. 프로젝트\Project1"
```

### 2. GitHub - 소스코드 업데이트

```powershell
git status
git add README.md
git add .
git commit -m "docs: README init"
git push origin main

git add 파일명_입력 && git commit -m "커밋메시지_입력"

Commit Conventional
  feat : 새 기능 추가, 의도대로 잘 돌아가지만 요구사항이 바뀐 것
  fix : 버그 수정, 의도한 대로 안 돌아가서 고친 것
  docs : 문서만 수정
  refactor : 동작은 그대로, 코드 구조만 개선
  chore : 잡다한거



```

### 3. 최초 커밋 시 (계정 설정)

```powershell
git config --global user.name "piglove06"
git config --global user.email "piglove06@hanmail.net"
```

### 4. 프롬프트 인젝션 자료 url
https://github.com/mlcommons/ailuminate/blob/main/airr_official_1.0_demo_fr_fr_prompt_set_release.csv 


### 5. 회사에서 자체LLM을 사용한다는 가정하에 고려해야할 사항

1. 사용자 비율, 사용자가 동시에 몰릴 때 처리방법
2. 하드웨어비용
3. 엔비디아 그래픽카드를 구하여 LLMOps vs 맥미니 여러대로 LLM Ops
4. 보안관련된 항목, 권한 등 추가작업
5. RAG, 튜닝, 툴콜링, 랭그래프등 구형 & 소형 모델일수록 순서와 통제를 강하게 할 필요가 있음.

### 6. 딥러닝기술중 수업에서 배운 기술과 최신형 모델들이 사용하는 기술 비교
1. Normalizer(RMSNorm)
2. Attention(GQA, MLA)
3. 트랜스포머
4. Embedding(RoPE)
5. 활성함수(SwiGLU)
6. Weight수정방식(AdamW)
7. 양자화(FP32 / BF16)
8. 학습방식(SFT / RLHF / DPO)
9. FFN관련(MoE)
10. CUDA를 효율적으로 사용 or 


test