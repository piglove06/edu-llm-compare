"""
STEP5 질문 10개를 readfiles 폴더의 문서(DOC-A, DOC-B)와 결합해
OpenAI GPT-5.6 Luna에 묻고 결과를 JSONL로 저장하는 스크립트.

사용법:
1. 이 파일과 같은 위치에 readfiles/ 폴더를 만들고 DOC-A*, DOC-B* 파일을 넣는다.
2. 실행 시 OpenAI API 키를 화면에 표시되지 않는 방식으로 입력한다.
3. 질문 10개를 Luna에 각각 한 번씩 보내고 결과를 저장한다.
"""

import json
import platform
import time
from datetime import datetime
from getpass import getpass
from importlib import metadata
from pathlib import Path
from uuid import uuid4

try:
    from openai import APIError, APITimeoutError, OpenAI
except ModuleNotFoundError:
    raise SystemExit(1)


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ------------------------------------------------------------------
# 설정
# ------------------------------------------------------------------
MODEL = "gpt-5.6-luna"
PROJECT_DIR = Path(__file__).resolve().parent
READFILES_DIR = PROJECT_DIR / "readfiles"
RESULT_FILE = PROJECT_DIR / "log_05_luna_document_qa.jsonl"

MODEL_OPTIONS = {
    "reasoning": {"effort": "none"},
    "max_output_tokens": 1024,
    "tools": [],
    "tool_choice": "none",
    "store": False,
}

MODEL_COMPARISON_INFO = {
    "model": MODEL,
    "service_type": "Cloud API",
    "license": "OpenAI API 서비스 약관 적용",
    "모델 최대 Context Length": 1_050_000,
    "최대 출력 토큰": 128_000,
    "model_card_source": "https://developers.openai.com/api/docs/models/gpt-5.6-luna",
}

SYSTEM_PROMPT = """
당신은 제공된 문서의 내용만 근거로 답하는 문서 질의 도우미입니다.

[근거 사용 규칙]
1. 답변은 사용자 메시지에 실제로 제공된 문서 내용만 근거로 작성합니다.
2. URL만 있고 웹페이지 본문이 제공되지 않았다면, 해당 URL을 열거나 내용을 확인했다고 말하지 않습니다.
3. 모델명, URL, 사전 학습 지식만으로 문서 내용을 추측하거나 만들어내지 않습니다.
4. 질문의 답이 문서에 없거나 정보가 부족하면 다음과 같이 명확히 답합니다.
   "제공된 문서에 해당 정보가 명시되어 있지 않습니다."
5. 날짜, 숫자, 파라미터 수, Context Length, 라이선스, 오류 코드 등은 문서에 적힌 값을 그대로 사용합니다.
6. 비슷한 용어 또는 다른 모델의 정보를 섞어서 답하지 않습니다.
7. 여러 문서가 제공되면 각 문서의 내용을 구분해서 설명합니다.
8. 공통점은 두 문서에서 실제로 확인할 수 있는 내용만 작성합니다.

[응답 형식 규칙]
1. 질문에서 요구한 문장 수, 답변 길이, 표 형식 등을 정확히 지킵니다.
2. 짧게 답하라는 질문에는 부가 설명을 추가하지 않습니다.
3. 표를 요청한 경우 마크다운 표만 출력하고 코드 블록으로 감싸지 않습니다.
4. 요청하지 않은 배경 설명, 예시, 코드, 결론은 추가하지 않습니다.
5. 한국어로 쉽고 명확하게 답합니다.
6. 답변하기 전에 문서에서 근거를 확인하되, 확인 과정이나 내부 판단 과정은 출력하지 않습니다.
""".strip()

GROUNDING_REMINDER = (
    "중요: 위에 제공된 문서만 근거로 답하세요. "
    "문서에 없는 내용은 추측하지 말고 명시되어 있지 않다고 답하세요."
)


# ------------------------------------------------------------------
# 질문 10개 세트
# ------------------------------------------------------------------

# 프롬프트 튜닝 전 질문 주석처리. 포맷이 다르니 사용시 수정필요.
# QUESTIONS = [
#     {
#         "id": "Q1",
#         "type": "비정상",
#         "sources": [],
#         "question": (
#             "문제1 : https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct "
#             "해당 URL에 있는 Model Card를 참고해서 초보자에게 쉽게 이해할 수 있게 설명해주세요."
#         ),
#         "note": "URL 접근 불가 상태에서 '읽은 척' 하는지(hallucination) 확인",
#     },
#     {
#         "id": "Q2",
#         "type": "정상(자유요약)",
#         "sources": ["DOC-A"],
#         "question": "문제2 : 이 문서 내용을 초보자도 이해하기 쉽게 핵심 특징 내용 추가하여 3~4문장으로 요약해 주세요.",
#         "note": "핵심 특징(하이브리드 어텐션, MoE 구조 등) 언급 여부",
#     },
#     {
#         "id": "Q3",
#         "type": "정상(사실추출)",
#         "sources": ["DOC-A"],
#         "question": "문제3 : 이 모델의 전체 파라미터 수와 실제 활성화되는 파라미터 수는 각각 몇 개인가요?",
#         "note": "정답: 125B(전체) / 6B(활성화)",
#     },
#     {
#         "id": "Q4",
#         "type": "정상(사실추출)",
#         "sources": ["DOC-A"],
#         "question": "문제4 : 이 모델의 기본 Context Length와 확장 가능한 최대 Context Length는 얼마인가요?",
#         "note": "정답: 262,144(기본) / 1,000,000(확장 시)",
#     },
#     {
#         "id": "Q5",
#         "type": "경계(지시이행)",
#         "sources": ["DOC-A"],
#         "question": "문제5 : 이 모델의 라이선스를 정확히 한 단어(또는 짧은 구)로만 답해 주세요.",
#         "note": "정답: qwen-community-1.0 계열. 'Apache' 등으로 지어내지 않는지",
#     },
#     {
#         "id": "Q6",
#         "type": "정보부족",
#         "sources": ["DOC-A"],
#         "question": "문제6 : 이 모델의 정확한 출시일(연/월/일)이 언제인가요?",
#         "note": "원문에 정확한 날짜 없음(월/년만 있음) -> '명시 안 됨'이라 답하는지",
#     },
#     {
#         "id": "Q7",
#         "type": "정상(자유요약)",
#         "sources": ["DOC-B"],
#         "question": "문제7 : 이 문서 내용을 초보자도 이해하기 쉽게 3~4문장으로 요약해 주세요.",
#         "note": "API 재시도/백오프/fallback 핵심 개념 언급 여부",
#     },
#     {
#         "id": "Q8",
#         "type": "정상(사실추출)",
#         "sources": ["DOC-B"],
#         "question": "문제8 : OpenAI Python SDK는 어떤 오류들을 기본적으로 몇 번 재시도하나요?",
#         "note": "정답: 연결 오류/408/409/429/5xx, 기본 2번",
#     },
#     {
#         "id": "Q9",
#         "type": "경계(비교종합)",
#         "sources": ["DOC-A", "DOC-B"],
#         "question": "문제9 : 두 문서는 각각 어떤 주제를 다루고 있나요? 공통점이 있다면 설명해 주세요.",
#         "note": "DOC-A(모델 아키텍처) vs DOC-B(API 안정성)를 정확히 구분하는지",
#     },
#     {
#         "id": "Q10",
#         "type": "경계(지시이행+형식)",
#         "sources": ["DOC-B"],
#         "question": "문제10 : 재시도가 불가능한(즉시 중단해야 하는) 대표적인 오류 3가지를 마크다운 표로 정리해 주세요.",
#         "note": "정답: 잘못된 API key, 400 Bad Request, permission denied 등. 표 형식 준수 여부",
#     },
# ]


QUESTIONS = [
    {
        "id": "Q1",
        "type": "비정상",
        "평가_기준": "URL 접근 불가 상태에서 '읽은 척' 하는지(hallucination) 확인",
        "source_doc_list": [],
        "question": (
            "문제1 : 다음 URL의 Model Card를 초보자가 이해하기 쉽게 설명해 주세요.\n"
            "URL: https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct\n\n"
            "현재 URL의 실제 본문이 제공되지 않았습니다. "
            "페이지 내용을 실제로 확인할 수 없다면 사전 지식으로 추측하지 말고, "
            "접근할 수 없어 확인이 필요하다고 1~2문장으로 답해 주세요."
        ),
    },
    {
        "id": "Q2",
        "type": "정상(자유요약)",
        "평가_기준": "핵심 특징(하이브리드 어텐션, MoE 구조 등) 언급 여부",
        "source_doc_list": ["DOC-A"],
        "question": (
            "문제2 : DOC-A에 명시된 내용만 사용하여 이 모델을 초보자가 이해하기 쉽게 "
            "정확히 3~4문장으로 요약해 주세요. 모델의 핵심 구조와 효율성 관련 특징을 "
            "포함하고, 문서에 없는 특징은 추가하지 마세요."
        ),
    },
    {
        "id": "Q3",
        "type": "정상(사실추출)",
        "평가_기준": "정답: 125B(전체) / 6B(활성화)",
        "source_doc_list": ["DOC-A"],
        "question": (
            "문제3 : DOC-A에서 이 모델의 전체 파라미터 수와 한 번의 추론에서 실제로 "
            "활성화되는 파라미터 수를 각각 찾아 주세요. "
            "'전체 파라미터: 값 / 활성 파라미터: 값' 형식으로 한 줄만 답하고, "
            "문서에 없는 수치는 추측하지 마세요."
        ),
    },
    {
        "id": "Q4",
        "type": "정상(사실추출)",
        "평가_기준": "정답: 262,144(기본) / 1,000,000(확장 시)",
        "source_doc_list": ["DOC-A"],
        "question": (
            "문제4 : DOC-A에서 이 모델의 기본 Context Length와 확장 가능한 최대 "
            "Context Length를 각각 찾아 주세요. "
            "'기본 Context Length: 값 / 확장 최대 Context Length: 값' 형식으로 "
            "한 줄만 답하고, 서로 다른 수치를 혼동하지 마세요."
        ),
    },
    {
        "id": "Q5",
        "type": "경계(지시이행)",
        "평가_기준": "정답: qwen-community-1.0 계열. 'Apache' 등으로 지어내지 않는지",
        "source_doc_list": ["DOC-A"],
        "question": (
            "문제5 : DOC-A의 라이선스 메타데이터에서 license_name 값을 확인하여 "
            "그 값을 그대로 답해 주세요. 설명, 문장, 마크다운을 추가하지 말고 "
            "라이선스 이름 한 개만 출력하세요."
        ),
    },
    {
        "id": "Q6",
        "type": "정보부족",
        "평가_기준": "원문에 정확한 날짜 없음(월/년만 있음) -> '명시 안 됨'이라 답하는지",
        "source_doc_list": ["DOC-A"],
        "question": (
            "문제6 : DOC-A에 이 모델의 정확한 출시일이 연/월/일 형식으로 명시되어 "
            "있는지 확인해 주세요. 정확한 날짜가 없다면 추측하거나 외부 지식을 사용하지 "
            "말고 '제공된 문서에 정확한 출시일(연/월/일)은 명시되어 있지 않습니다.'라고 "
            "한 문장으로 답해 주세요."
        ),
    },
    {
        "id": "Q7",
        "type": "정상(자유요약)",
        "평가_기준": "API 재시도/백오프/fallback 핵심 개념 언급 여부",
        "source_doc_list": ["DOC-B"],
        "question": (
            "문제7 : DOC-B에 명시된 내용만 사용하여 초보자가 이해하기 쉽게 정확히 "
            "3~4문장으로 요약해 주세요. API 재시도, 백오프, fallback의 역할을 "
            "포함하되 문서에 없는 동작이나 설정은 추가하지 마세요."
        ),
    },
    {
        "id": "Q8",
        "type": "정상(사실추출)",
        "평가_기준": "정답: 연결 오류/408/409/429/5xx, 기본 2번",
        "source_doc_list": ["DOC-B"],
        "question": (
            "문제8 : DOC-B에서 OpenAI Python SDK가 기본적으로 재시도하는 오류의 "
            "종류와 기본 재시도 횟수를 찾아 주세요. "
            "'재시도 대상: 값 / 기본 재시도 횟수: 값' 형식으로 간결하게 답하고, "
            "문서에 없는 오류나 횟수는 추가하지 마세요."
        ),
    },
    {
        "id": "Q9",
        "type": "경계(비교종합)",
        "평가_기준": "DOC-A(모델 아키텍처) vs DOC-B(API 안정성)를 정확히 구분하는지",
        "source_doc_list": ["DOC-A", "DOC-B"],
        "question": (
            "문제9 : DOC-A와 DOC-B의 주제를 서로 섞지 말고 다음 형식으로 설명해 주세요.\n"
            "- DOC-A: 해당 문서가 다루는 주제\n"
            "- DOC-B: 해당 문서가 다루는 주제\n"
            "- 공통점: 두 문서에서 실제로 확인할 수 있는 공통점\n"
            "공통점을 확인하기 어렵다면 억지로 만들지 말고 "
            "'직접적인 공통점은 확인하기 어렵습니다.'라고 답해 주세요."
        ),
    },
    {
        "id": "Q10",
        "type": "경계(지시이행+형식)",
        "평가_기준": "정답: 잘못된 API key, 400 Bad Request, permission denied 등. 표 형식 준수 여부",
        "source_doc_list": ["DOC-B"],
        "question": (
            "문제10 : DOC-B에 명시된 재시도가 불가능하여 즉시 중단해야 하는 대표적인 "
            "오류를 정확히 3개 선택해 마크다운 표로 작성해 주세요. 표의 열은 '오류'와 "
            "'즉시 중단해야 하는 이유' 두 개만 사용하세요. 표 앞뒤에 설명을 추가하지 "
            "말고, 마크다운 코드 블록으로 감싸지 마세요."
        ),
    },
]


# ------------------------------------------------------------------
# 파일 읽기
# ------------------------------------------------------------------
def read_md_or_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError:
        raise RuntimeError("PDF를 읽으려면 pypdf 패키지가 필요합니다.")

    reader = PdfReader(str(path))
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def read_document(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in (".md", ".txt"):
        return read_md_or_txt(path)
    if suffix == ".pdf":
        return read_pdf(path)
    raise ValueError(f"지원하지 않는 파일 형식입니다: {suffix}")


def find_doc_files() -> dict[str, Path]:
    if not READFILES_DIR.exists():
        READFILES_DIR.mkdir(parents=True, exist_ok=True)
        return {}

    mapping = {}
    for path in READFILES_DIR.iterdir():
        if not path.is_file() or path.suffix.lower() not in (".md", ".txt", ".pdf"):
            continue
        stem_upper = path.stem.upper()
        if stem_upper.startswith("DOC-A"):
            mapping["DOC-A"] = path
        elif stem_upper.startswith("DOC-B"):
            mapping["DOC-B"] = path
    return mapping


def load_doc_texts(doc_files: dict[str, Path]) -> dict[str, str]:
    texts = {}
    for key, path in doc_files.items():
        try:
            texts[key] = read_document(path)
        except Exception:
            continue
    return texts


def build_prompt(question: dict, doc_texts: dict[str, str]) -> str:
    if not question["source_doc_list"]:
        return question["question"]

    parts = []
    for source in question["source_doc_list"]:
        text = doc_texts.get(source, "")
        parts.append(
            f"----- {source} 문서 시작 -----\n{text}\n----- {source} 문서 끝 -----"
        )
    documents = "\n\n".join(parts)
    return (
        f"다음은 문서 내용입니다.\n\n{documents}\n\n"
        f"{GROUNDING_REMINDER}\n\n{question['question']}"
    )


# ------------------------------------------------------------------
# 환경·결과 정보
# ------------------------------------------------------------------
def package_version(name: str):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def get_env_info() -> dict:
    return {
        "python_version": platform.python_version(),
        "os": platform.platform(),
        "package_versions": {
            "openai": package_version("openai"),
            "pypdf": package_version("pypdf"),
        },
    }


def summarize(results: list[dict]) -> dict:
    successful = [result for result in results if result["status"] == "성공"]
    metrics = {}
    for key in ("응답시간_초", "입력_토큰수", "출력_토큰수"):
        values = [result[key] for result in successful if isinstance(result.get(key), (int, float))]
        metrics[key] = {
            "평균": sum(values) / len(values) if values else None,
            "n": len(values),
        }

    return {
        MODEL: {
            "성공_수": len(successful),
            "시도_수": sum(result["status"] != "건너뜀" for result in results),
            "건너뜀_수": sum(result["status"] == "건너뜀" for result in results),
            "실패_수": sum(result["status"] == "실패" for result in results),
            "중단_수": sum(result["status"] == "중단" for result in results),
            "성공결과_지표": metrics,
        }
    }


def append_run(run: dict) -> None:
    with RESULT_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(run, ensure_ascii=False) + "\n")


def main() -> None:
    print("05_luna_document_qa.py 파일 실행")

    api_key = getpass("OpenAI API 키를 붙여넣고 Enter (화면에 보이지 않음): ").strip()
    if not api_key:
        raise SystemExit("키를 입력하지 않아 API를 호출하지 않았습니다.")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.openai.com/v1",
        timeout=180,
        max_retries=0,
    )

    run = {
        "completed_timestamp": None,
        "status": "진행 중",
        "common_info": {
            "models": [MODEL],
            "question_count": len(QUESTIONS),
            "planned_result_count": len(QUESTIONS),
            "result_count": 0,
            "env_info": get_env_info(),
            "model_comparison_info": [MODEL_COMPARISON_INFO],
        },
        "results": [],
        "summary": {},
    }

    try:
        doc_texts = load_doc_texts(find_doc_files())

        for question in QUESTIONS:
            missing = sorted(set(question["source_doc_list"]) - set(doc_texts))
            prompt = build_prompt(question, doc_texts) if not missing else None
            record = {
                "execution_id": str(uuid4()),
                "question_id": question["id"],
                "question_type": question["type"],
                "평가_기준": question.get("평가_기준"),
                "source_doc_list": question["source_doc_list"],
                "model": MODEL,
                "settings": dict(MODEL_OPTIONS),
                # 로그에는 질문만 저장하고 API 입력에는 문서 본문도 포함합니다.
                "prompt": question["question"],
                "prompt_char_count": len(prompt) if prompt is not None else None,
            }

            if missing:
                record.update(
                    status="건너뜀",
                    error="문서 없음/읽기 실패: " + ", ".join(missing),
                )
            else:
                started = time.perf_counter()
                try:
                    response = client.responses.create(
                        model=MODEL,
                        instructions=SYSTEM_PROMPT,
                        input=prompt,
                        **MODEL_OPTIONS,
                    )
                    record["응답시간_초"] = round(time.perf_counter() - started, 4)
                    record["status"] = "성공" if response.status == "completed" else "미완료"
                    record["response"] = response.output_text or ""
                    record["API_처리상태"] = response.status

                    usage = response.usage
                    record["입력_토큰수"] = getattr(usage, "input_tokens", None)
                    record["출력_토큰수"] = getattr(usage, "output_tokens", None)

                    incomplete = getattr(response, "incomplete_details", None)
                    if incomplete is not None:
                        record["미완료_상세"] = (
                            incomplete.model_dump(mode="json")
                            if hasattr(incomplete, "model_dump")
                            else str(incomplete)
                        )
                except APITimeoutError as error:
                    record.update(
                        status="실패",
                        응답시간_초=round(time.perf_counter() - started, 4),
                        error_type=type(error).__name__,
                        error="응답 대기 시간 초과",
                    )
                except APIError as error:
                    record.update(
                        status="실패",
                        응답시간_초=round(time.perf_counter() - started, 4),
                        error_type=type(error).__name__,
                        error=str(error),
                        http_status=getattr(error, "status_code", None),
                    )
                except Exception as error:
                    record.update(
                        status="실패",
                        응답시간_초=round(time.perf_counter() - started, 4),
                        error_type=type(error).__name__,
                        error=str(error),
                    )
                except KeyboardInterrupt:
                    record.update(
                        status="중단",
                        응답시간_초=round(time.perf_counter() - started, 4),
                    )
                    run["results"].append(record)
                    raise

            run["results"].append(record)
            run["common_info"]["result_count"] = len(run["results"])

        run["status"] = (
            "완료"
            if all(result["status"] == "성공" for result in run["results"])
            else "완료(실패/건너뜀/미완료 포함)"
        )
    except KeyboardInterrupt:
        run["status"] = "중단"
    except Exception as error:
        run.update(
            status="실패",
            error_type=type(error).__name__,
            error=str(error),
        )
    finally:
        run["completed_timestamp"] = now_str()
        run["common_info"]["result_count"] = len(run["results"])
        run["summary"] = summarize(run["results"])
        append_run(run)
        print("05_luna_document_qa.py 파일 종료")


if __name__ == "__main__":
    main()
