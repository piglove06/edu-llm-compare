"""
STEP5 질문 10개 세트를 readfiles 폴더의 문서(DOC-A, DOC-B)와 결합해
두 모델(exaone3.5, granite4.1)에 각각 묻고 결과를 저장하는 스크립트.

사용법:
1. 이 파일과 같은 위치에 readfiles/ 폴더를 만들고, 아래 두 파일을 넣는다.
   - DOC-A.md  (또는 DOC-A로 시작하는 md/txt/pdf 파일)
   - DOC-B.pdf (또는 DOC-B로 시작하는 md/txt/pdf 파일)
2. QUESTIONS 리스트를 필요에 맞게 수정한다 (질문 ID/문서/질문 내용).
3. 실행하면 질문 10개 x 모델 2개 = 총 20회 호출이 이루어지고 결과가 저장된다.
"""

import sys
import time
import platform
import subprocess
import json
import tomllib
from uuid import uuid4
from pathlib import Path
from datetime import datetime


def now_str() -> str:
    """가독성 좋은 타임스탬프: 2026-09-14 17:40:23"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


try:
    import ollama
    from ollama import Client
except ModuleNotFoundError:
    raise SystemExit(1)

# ------------------------------------------------------------------
# 설정
# ------------------------------------------------------------------
MODELS = [
    "exaone3.5:7.8b",
    "granite4.1:3b",
]

READFILES_DIR = Path(__file__).parent / "readfiles"
PROJECT_DIR = Path(__file__).resolve().parent
RESULT_FILE = PROJECT_DIR / "log_04_document_qa.jsonl"
MODEL_OPTIONS = {m: {"temperature": 0, "num_predict": 1024, "num_ctx": 8192} for m in MODELS}
MODEL_REFERENCES = {m: {"license": None, "모델 최대 Context Length": None} for m in MODELS}
# 사용자가 제공한 라이선스 표기. 공식 출처 URL은 확인 후 위 항목에 입력합니다.
MODEL_REFERENCES["exaone3.5:7.8b"]["license"] = "EXAONE AI Model License Agreement 1.1 - NC"
MODEL_REFERENCES["exaone3.5:7.8b"]["모델 최대 Context Length"] = 32768
MODEL_REFERENCES["granite4.1:3b"]["license"] = "Apache 2.0"
MODEL_REFERENCES["granite4.1:3b"]["모델 최대 Context Length"] = 131072


client = Client(host="http://127.0.0.1:11434", timeout=180)

# ------------------------------------------------------------------
# STEP5 질문 10개 세트
# "source_doc_list": 이 질문에 함께 제공할 문서 키 목록. 빈 리스트면 문서 없이 질문만 던짐(Q1 비정상 사례).
# ------------------------------------------------------------------
QUESTIONS = [
    {
        "id": "Q1",
        "type": "비정상",
        "평가_기준": "URL 접근 불가 상태에서 '읽은 척' 하는지(hallucination) 확인",
        "source_doc_list": [],
        "question": (
            "문제1 : https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct "
            "해당 URL에 있는 Model Card를 참고해서 초보자에게 쉽게 이해할 수 있게 설명해주세요."
        ),
    },
    {
        "id": "Q2",
        "type": "정상(자유요약)",
        "평가_기준": "핵심 특징(하이브리드 어텐션, MoE 구조 등) 언급 여부",
        "source_doc_list": ["DOC-A"],
        "question": "문제2 : 이 문서 내용을 초보자도 이해하기 쉽게 핵심 특징 내용 추가하여 3~4문장으로 요약해 주세요.",
    },
    {
        "id": "Q3",
        "type": "정상(사실추출)",
        "평가_기준": "정답: 125B(전체) / 6B(활성화)",
        "source_doc_list": ["DOC-A"],
        "question": "문제3 : 이 모델의 전체 파라미터 수와 실제 활성화되는 파라미터 수는 각각 몇 개인가요?",
    },
    {
        "id": "Q4",
        "type": "정상(사실추출)",
        "평가_기준": "정답: 262,144(기본) / 1,000,000(확장 시)",
        "source_doc_list": ["DOC-A"],
        "question": "문제4 : 이 모델의 기본 Context Length와 확장 가능한 최대 Context Length는 얼마인가요?",
    },
    {
        "id": "Q5",
        "type": "경계(지시이행)",
        "평가_기준": "정답: qwen-community-1.0 계열. 'Apache' 등으로 지어내지 않는지",
        "source_doc_list": ["DOC-A"],
        "question": "문제5 : 이 모델의 라이선스를 정확히 한 단어(또는 짧은 구)로만 답해 주세요.",
    },
    {
        "id": "Q6",
        "type": "정보부족",
        "평가_기준": "원문에 정확한 날짜 없음(월/년만 있음) -> '명시 안 됨'이라 답하는지",
        "source_doc_list": ["DOC-A"],
        "question": "문제6 : 이 모델의 정확한 출시일(연/월/일)이 언제인가요?",
    },
    {
        "id": "Q7",
        "type": "정상(자유요약)",
        "평가_기준": "API 재시도/백오프/fallback 핵심 개념 언급 여부",
        "source_doc_list": ["DOC-B"],
        "question": "문제7 : 이 문서 내용을 초보자도 이해하기 쉽게 3~4문장으로 요약해 주세요.",
    },
    {
        "id": "Q8",
        "type": "정상(사실추출)",
        "평가_기준": "정답: 연결 오류/408/409/429/5xx, 기본 2번",
        "source_doc_list": ["DOC-B"],
        "question": "문제8 : OpenAI Python SDK는 어떤 오류들을 기본적으로 몇 번 재시도하나요?",
    },
    {
        "id": "Q9",
        "type": "경계(비교종합)",
        "평가_기준": "DOC-A(모델 아키텍처) vs DOC-B(API 안정성)를 정확히 구분하는지",
        "source_doc_list": ["DOC-A", "DOC-B"],
        "question": "문제9 : 두 문서는 각각 어떤 주제를 다루고 있나요? 공통점이 있다면 설명해 주세요.",
    },
    {
        "id": "Q10",
        "type": "경계(지시이행+형식)",
        "평가_기준": "정답: 잘못된 API key, 400 Bad Request, permission denied 등. 표 형식 준수 여부",
        "source_doc_list": ["DOC-B"],
        "question": "문제10 : 재시도가 불가능한(즉시 중단해야 하는) 대표적인 오류 3가지를 마크다운 표로 정리해 주세요.",
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
        raise RuntimeError(
            "PDF를 읽으려면 pypdf 패키지가 필요합니다. 설치: pip install pypdf"
        )
    reader = PdfReader(str(path))
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def read_document(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in (".md", ".txt"):
        return read_md_or_txt(path)
    elif suffix == ".pdf":
        return read_pdf(path)
    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {suffix}")


def find_doc_files() -> dict[str, Path]:
    """readfiles 폴더에서 'DOC-A', 'DOC-B'로 시작하는 파일을 찾아 매핑합니다."""
    if not READFILES_DIR.exists():
        READFILES_DIR.mkdir(parents=True, exist_ok=True)
        return {}

    mapping = {}
    for p in READFILES_DIR.iterdir():
        if not p.is_file() or p.suffix.lower() not in (".md", ".txt", ".pdf"):
            continue
        stem_upper = p.stem.upper()
        if stem_upper.startswith("DOC-A"):
            mapping["DOC-A"] = p
        elif stem_upper.startswith("DOC-B"):
            mapping["DOC-B"] = p
    return mapping


def load_doc_texts(doc_files: dict[str, Path]) -> dict[str, str]:
    texts = {}
    for key, path in doc_files.items():
        try:
            texts[key] = read_document(path)
        except Exception:
            continue
    return texts


def build_prompt(q: dict, doc_texts: dict[str, str]) -> str:
    """질문에 필요한 문서를 프롬프트 앞에 붙여서 완성된 질문 텍스트를 만듭니다."""
    if not q["source_doc_list"]:
        return q["question"]

    parts = []
    for src in q["source_doc_list"]:
        text = doc_texts.get(src, "")
        parts.append(f"----- {src} 문서 시작 -----\n{text}\n----- {src} 문서 끝 -----")

    docs_block = "\n\n".join(parts)
    return f"다음은 문서 내용입니다.\n\n{docs_block}\n\n{q['question']}"


# ------------------------------------------------------------------
# 환경 정보
# ------------------------------------------------------------------


def get_ollama_model_vram(model_name):
    try:
        ps_info = client.ps()

        for m in ps_info.models:
            if m.name == model_name:
                size_vram_bytes = m.size_vram

                return {
                    "size_vram_bytes": size_vram_bytes,
                    "size_vram_mib": round(size_vram_bytes / 1024 / 1024, 2),
                }

        return {
            "size_vram_bytes": None,
            "size_vram_mib": None,
            "note": "client.ps()에서 해당 모델을 찾지 못함",
        }

    except Exception as e:
        return {
            "size_vram_bytes": None,
            "size_vram_mib": None,
            "note": f"VRAM 확인 실패: {e}",
        }

def get_gpu_info():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        return "nvidia-smi 실행됨, 그러나 GPU 정보 없음"
    except FileNotFoundError:
        return "nvidia-smi 없음 (GPU 미인식 또는 CPU 환경)"
    except Exception as e:
        return f"GPU 정보 확인 실패: {e}"


def get_env_info():
    pyproject_data = {}
    try:
        raw = (PROJECT_DIR / "pyproject.toml").read_bytes()
        pyproject_data = tomllib.loads(raw.decode("utf-8-sig"))
    except Exception:
        pass

    # 실행 파일과 같은 폴더의 pyproject.toml에 선언된 직접 의존성만 기록합니다.
    versions = {}
    for dependency in pyproject_data.get("project", {}).get("dependencies", []):
        if "==" in dependency:
            package_name, package_version = dependency.split("==", 1)
            versions[package_name.strip()] = package_version.strip()
        else:
            versions[dependency] = "버전 미고정"
    try:
        server = client._request_raw("GET", "/api/version").json().get("version")
    except Exception:
        server = None
    return {"python_version": platform.python_version(), "os": platform.platform(),
            "package_versions": versions, "ollama_server_version": server,
            "프로그램 시작 시 PC 전체 VRAM 사용량": get_gpu_info()}


def get_model_info(model):
    info = {"model": model, **MODEL_REFERENCES[model]}
    try:
        data = client.show(model).model_dump(mode="json")
        info["quantization"] = (data.get("details") or {}).get("quantization_level")
    except Exception as error:
        info["metadata_error"] = str(error)
    return info


def summarize(results):
    summary = {}
    for model in MODELS:
        rows = [r for r in results if r["model"] == model]
        success = [r for r in rows if r["status"] == "성공"]
        metrics = {}
        for key in ("응답시간_초", "모델_로딩시간_초", "출력_토큰수", "초당_생성_토큰수"):
            values = [r[key] for r in success if isinstance(r.get(key), (int, float))]
            metrics[key] = {"평균": sum(values) / len(values) if values else None, "n": len(values)}
        vram_values = [r.get("ollama_model_vram", {}).get("size_vram_mib") for r in success]
        vram_values = [v for v in vram_values if isinstance(v, (int, float))]
        metrics["size_vram_mib"] = {
            "평균": sum(vram_values) / len(vram_values) if vram_values else None,
        }
        summary[model] = {
            "성공_수": len(success),
            "시도_수": sum(r["status"] != "건너뜀" for r in rows),
            "건너뜀_수": sum(r["status"] == "건너뜀" for r in rows),
            "실패_수": sum(r["status"] == "실패" for r in rows),
            "중단_수": sum(r["status"] == "중단" for r in rows),
            "성공결과_지표": metrics,
        }
    return summary


def append_run(run):
    """기존 JSONL 기록을 유지하고 현재 실행 결과를 새 줄에 추가합니다."""
    with RESULT_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(run, ensure_ascii=False) + "\n")


def main():
    print("04_document_qa.py 파일 실행")
    run = {
        "completed_timestamp": None, "status": "진행 중",
        "common_info": {
            "models": MODELS, "question_count": len(QUESTIONS),
            "planned_result_count": len(QUESTIONS) * len(MODELS),
            "result_count": 0, "env_info": get_env_info(),
            "model_comparison_info": [],
        }, "results": [], "summary": {},
    }
    try:
        client.list()
        run["common_info"]["model_comparison_info"] = [get_model_info(m) for m in MODELS]
        texts = load_doc_texts(find_doc_files())
        for q in QUESTIONS:
            missing = sorted(set(q["source_doc_list"]) - set(texts))
            prompt = build_prompt(q, texts) if not missing else None
            for model in MODELS:
                    record = {
                        "execution_id": str(uuid4()),
                        "question_id": q["id"], "question_type": q["type"],
                        "평가_기준": q.get("평가_기준"),
                        "source_doc_list": q["source_doc_list"],
                        "model": model,
                        "settings": dict(MODEL_OPTIONS[model]),
                        # 로그에는 질문만 저장합니다. 실제 모델 입력에는 문서 본문도 포함합니다.
                        "prompt": q["question"],
                        "prompt_char_count": len(prompt) if prompt is not None else None,
                    }
                    if missing:
                        record.update(status="건너뜀", error="문서 없음/읽기 실패: " + ", ".join(missing))
                    else:
                        start = time.perf_counter()
                        try:
                            response = client.chat(model=model, messages=[{"role": "user", "content": prompt}],
                                                   stream=False, options=record["settings"])
                            record["응답시간_초"] = round(time.perf_counter() - start, 4)
                            record["ollama_model_vram"] = get_ollama_model_vram(model)
                            record.update(status="성공", response=response.message.content)
                            record["입력_토큰수"] = getattr(response, "prompt_eval_count", None)
                            record["출력_토큰수"] = getattr(response, "eval_count", None)
                            record["생성_종료_이유"] = getattr(response, "done_reason", None)
                            generation_ns = getattr(response, "eval_duration", None)
                            loading_ns = getattr(response, "load_duration", None)
                            record["생성시간_초"] = generation_ns / 1e9 if generation_ns is not None else None
                            record["모델_로딩시간_초"] = loading_ns / 1e9 if loading_ns is not None else None
                            count = record["출력_토큰수"]
                            record["초당_생성_토큰수"] = count / (generation_ns / 1e9) if count is not None and generation_ns and generation_ns > 0 else None
                        except Exception as error:
                            record.update(status="실패", 응답시간_초=round(time.perf_counter() - start, 4),
                                          error_type=type(error).__name__, error=str(error))
                        except KeyboardInterrupt:
                            record.update(status="중단", 응답시간_초=round(time.perf_counter() - start, 4))
                            run["results"].append(record)
                            raise
                    run["results"].append(record)
                    run["common_info"]["result_count"] = len(run["results"])
        run["status"] = "완료" if all(r["status"] == "성공" for r in run["results"]) else "완료(실패/건너뜀 포함)"
    except KeyboardInterrupt:
        run["status"] = "중단"
    except Exception as error:
        run.update(status="실패", error_type=type(error).__name__, error=str(error))
    finally:
        run["completed_timestamp"] = now_str()
        run["common_info"]["result_count"] = len(run["results"])
        run["summary"] = summarize(run["results"])
        append_run(run)
        print("04_document_qa.py 파일 종료")


if __name__ == "__main__":
    main()
