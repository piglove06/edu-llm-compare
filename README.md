# edu-llm-compare

Private LLM 국비지원 과정 실습 프로젝트 — 로컬 LLM 2개(Qwen3, EXAONE3.5) + Cloud API 1개를 문서 분석 태스크로 비교하여 최종 모델 1개를 선정합니다.

---

## STEP 0. 모델 설치 및 실행

### exaone3.5:7.8b
- Hugging Face: https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct

```powershell
ollama pull exaone3.5:7.8b
ollama run exaone3.5:7.8b
ollama stop exaone3.5:7.8b
```

### qwen3:4b-instruct-2507-q4_K_M
- Hugging Face: https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507

```powershell
ollama pull qwen3:4b-instruct-2507-q4_K_M
ollama run qwen3:4b-instruct-2507-q4_K_M
ollama stop qwen3:4b-instruct-2507-q4_K_M
```

### 설치 확인 (`ollama list`)

| NAME | ID | SIZE | MODIFIED |
|---|---|---|---|
| exaone3.5:7.8b | c7c4e3d1ca22 | 4.8 GB | About an hour ago |
| qwen3:4b-instruct-2507-q4_K_M | 0edcdef34593 | 2.5 GB | 4 days ago |

---

## STEP 1. 문제 정의 (완료)

**문서분석모델**

- **Target**: 
  - Private LLM수업을 듣는 학생
- **사용목적**:
  - 현재 Private LLM수업 시 내용분석 및 어려운 내용을 쉽게 설명받고 싶음.
  - 수업자료 예습 및 복습을 위한 수업자료 내용을 쉽게 설명, 요약, 전체적인 흐름 요청
  - GitHub, Hugging Face 내용분석
- **사용시점**:
  - 수업시작 전 및 쉬는시간에 다음수업 예습 시 사용
  - 수업이 끝난 이후 복습
  - 수업이 끝난 이후 수업과 관련된 GitHub, Hugging Face의 내용분석
  
- **발전가능성**:
  - 각 LLM이 내 수업질문과 수업자료를 통해 내가 얼마나 해당과목을 이해하고 있는지 확인가능
  - LLM이 각 파트별 사용자의 학습여부를 수치화하여 저장 후, 난이도에 맞는 문제출제 및 심화과정 추가학습

- **사용환경**:
  - 수업용 노트북
  - GPU: NVIDIA GeForce RTX 5060 Laptop GPU (8GB VRAM)
  - CPU: Intel(R) Core(TM) Ultra 9 275HX (2.70 GHz)
  - OS: Windows 11 Pro 64비트
  - RAM: DDR5
  - 저장장치: 1TB (954 GB 중 174 GB 사용됨)

---

## STEP 2. 모델 요구사항 정의 (확정)

### 필수 통과 조건

| 조건 | 확인 방법 | Qwen3:4B | EXAONE3.5:7.8B |
|---|---|---|---|
| RTX 5060(8GB VRAM) 노트북에서 실행 가능 | `ollama run`으로 정상 구동 확인 | ✅ (2.5GB, 실행 확인됨) | ✅ (4.8GB, 실행 확인됨) |
| 연구/개인 학습 목적 사용 가능한 라이선스 | 라이선스 확인 | ✅ Apache 2.0 | ✅ EXAONE 1.1-NC (비상업 연구/학습 목적 한정 — 본 프로젝트 용도 문제없음) |
| md/PDF 문서 길이를 수용하는 Context Length | Model Card 확인 | ✅ 262,144 토큰 | ✅ 32,768 토큰 |
| 한국어 질문 → 한국어 답변 기본 동작 | 프롬프트 입력하여 확인 | ✅ 한국어 응답 확인됨 | ✅ 한국어 응답 확인됨 |
| Instruct/Chat 태스크 지원 | Model Card 확인 | ✅ | ✅ |

→ **두 후보 모두 필수 통과 조건을 전부 충족** — 본격 비교 실험(STEP5~6)으로 넘어갈 준비 완료

### 선호 우선순위

1. **할루시네이션이 없는 결과물** — 원문에 없는 내용을 지어내지 않고, 모르면 모른다고 물어보는지 확인
2. **사용자가 판단하에 원하는 결과물** — 지시(요약/설명/지정 항목 질의)를 얼마나 정확히 이행하는지 여부
3. **속도** — 응답 시간 및 VRAM 사용량(우선순위 낮음)


## STEP 3. 후보 모델 탐색

## STEP 4. 모델 실행 환경 확인과 Python 연결

## STEP 5. 평가 질문과 품질 기준 확정

## STEP 6. 로컬 모델 품질/성능 측정

### 선택 실습 A. Quantization 비교

### 선택 실습 B. Embedding 실험

## STEP 7. Open-source LLM vs Cloud API 비교

## STEP 8. 최종 모델 선정 및 발표

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

## 참고 URL

1. [edu-llm-compare (프로젝트 저장소)](https://github.com/piglove06/edu-llm-compare.git)
2. HF 모델 정보
   - [EXAONE-3.5-7.8B-Instruct](https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct)
   - [Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
3. EXAONE-3.5-7.8B 라이선스 원문
   - [EXAONE AI Model License Agreement 1.1 - NC](https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct/blob/main/LICENSE)

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
git commit -m "docs: README init"
git push origin main
```

### 3. 최초 커밋 시 (계정 설정)

```powershell
git config --global user.name "piglove06"
git config --global user.email "piglove06@hanmail.net"
```