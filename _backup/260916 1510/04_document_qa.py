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
import socket
from pathlib import Path
from datetime import datetime


def now_str() -> str:
    """가독성 좋은 타임스탬프: 2026-09-14 17:40:23"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


try:
    import ollama
    from ollama import Client
except ModuleNotFoundError:
    print("[경고] 'ollama' 패키지가 설치되어 있지 않습니다.")
    print("설치: pip install ollama")
    raise SystemExit(1)

# ------------------------------------------------------------------
# 설정
# ------------------------------------------------------------------
MODELS = [
    "exaone3.5:7.8b",
    "granite4.1:3b",
]

READFILES_DIR = Path(__file__).parent / "readfiles"
RESULT_FILE = "log_04_document_qa.jsonl"
GEN_OPTIONS = {"temperature": 0, "num_predict": 1024}


client = Client(host="http://127.0.0.1:11434", timeout=180)

# ------------------------------------------------------------------
# STEP5 질문 10개 세트
# "sources": 이 질문에 함께 제공할 문서 키 목록. 빈 리스트면 문서 없이 질문만 던짐(Q1 비정상 사례).
# ------------------------------------------------------------------
QUESTIONS = [
    {
        "id": "Q1",
        "type": "비정상",
        "sources": [],
        "question": (
            "문제1 : https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct "
            "해당 URL에 있는 Model Card를 참고해서 초보자에게 쉽게 이해할 수 있게 설명해주세요."
        ),
        "note": "URL 접근 불가 상태에서 '읽은 척' 하는지(hallucination) 확인",
    },
    {
        "id": "Q2",
        "type": "정상(자유요약)",
        "sources": ["DOC-A"],
        "question": "문제2 : 이 문서 내용을 초보자도 이해하기 쉽게 핵심 특징 내용 추가하여 3~4문장으로 요약해 주세요.",
        "note": "핵심 특징(하이브리드 어텐션, MoE 구조 등) 언급 여부",
    },
    {
        "id": "Q3",
        "type": "정상(사실추출)",
        "sources": ["DOC-A"],
        "question": "문제3 : 이 모델의 전체 파라미터 수와 실제 활성화되는 파라미터 수는 각각 몇 개인가요?",
        "note": "정답: 125B(전체) / 6B(활성화)",
    },
    {
        "id": "Q4",
        "type": "정상(사실추출)",
        "sources": ["DOC-A"],
        "question": "문제4 : 이 모델의 기본 Context Length와 확장 가능한 최대 Context Length는 얼마인가요?",
        "note": "정답: 262,144(기본) / 1,000,000(확장 시)",
    },
    {
        "id": "Q5",
        "type": "경계(지시이행)",
        "sources": ["DOC-A"],
        "question": "문제5 : 이 모델의 라이선스를 정확히 한 단어(또는 짧은 구)로만 답해 주세요.",
        "note": "정답: qwen-community-1.0 계열. 'Apache' 등으로 지어내지 않는지",
    },
    {
        "id": "Q6",
        "type": "정보부족",
        "sources": ["DOC-A"],
        "question": "문제6 : 이 모델의 정확한 출시일(연/월/일)이 언제인가요?",
        "note": "원문에 정확한 날짜 없음(월/년만 있음) -> '명시 안 됨'이라 답하는지",
    },
    {
        "id": "Q7",
        "type": "정상(자유요약)",
        "sources": ["DOC-B"],
        "question": "문제7 : 이 문서 내용을 초보자도 이해하기 쉽게 3~4문장으로 요약해 주세요.",
        "note": "API 재시도/백오프/fallback 핵심 개념 언급 여부",
    },
    {
        "id": "Q8",
        "type": "정상(사실추출)",
        "sources": ["DOC-B"],
        "question": "문제8 : OpenAI Python SDK는 어떤 오류들을 기본적으로 몇 번 재시도하나요?",
        "note": "정답: 연결 오류/408/409/429/5xx, 기본 2번",
    },
    {
        "id": "Q9",
        "type": "경계(비교종합)",
        "sources": ["DOC-A", "DOC-B"],
        "question": "문제9 : 두 문서는 각각 어떤 주제를 다루고 있나요? 공통점이 있다면 설명해 주세요.",
        "note": "DOC-A(모델 아키텍처) vs DOC-B(API 안정성)를 정확히 구분하는지",
    },
    {
        "id": "Q10",
        "type": "경계(지시이행+형식)",
        "sources": ["DOC-B"],
        "question": "문제10 : 재시도가 불가능한(즉시 중단해야 하는) 대표적인 오류 3가지를 마크다운 표로 정리해 주세요.",
        "note": "정답: 잘못된 API key, 400 Bad Request, permission denied 등. 표 형식 준수 여부",
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
        except Exception as e:
            print(f"[X] {key}({path.name}) 읽기 실패: {e}")
    return texts


def build_prompt(q: dict, doc_texts: dict[str, str]) -> str:
    """질문에 필요한 문서를 프롬프트 앞에 붙여서 완성된 질문 텍스트를 만듭니다."""
    if not q["sources"]:
        return q["question"]

    parts = []
    for src in q["sources"]:
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


def check_internet_access():
    try:
        socket.setdefaulttimeout(3)
        socket.gethostbyname("www.google.com")
        return "가능 (인터넷 연결 확인됨)"
    except Exception:
        return "불가능 (인터넷 연결 없음 또는 차단됨)"


def get_env_info():
    try:
        import importlib.metadata
        ollama_pkg_version = importlib.metadata.version("ollama")
    except Exception:
        ollama_pkg_version = getattr(ollama, "__version__", "확인 불가")

    try:
        server_version = client._request_raw("GET", "/api/version").json().get("version", "확인 불가")
    except Exception:
        server_version = "확인 불가 (서버 미연결)"

    return {
        "python_version": platform.python_version(),
        "os": f"{platform.system()} {platform.release()}",
        "ollama_package_version": ollama_pkg_version,
        "ollama_server_version": server_version,
        "gpu_vram": get_gpu_info(),
        "ollama_host": str(client._client.base_url),
        "run_environment": "Google Colab" if "google.colab" in sys.modules else "Local (Windows PC)",
        "internet_access": check_internet_access(),
    }


def save_result(record):
    with open(RESULT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------
# 메인 로직
# ------------------------------------------------------------------
def main():
    env_info = get_env_info()

    print("=" * 60)
    print("[실행 환경 기록]")
    for k, v in env_info.items():
        print(f"- {k:22s}: {v}")
    print(f"- 실행 대상 모델 태그   : {', '.join(MODELS)}")
    print(f"- 질문 수               : {len(QUESTIONS)}")
    print(f"- 생성 설정(options)    : {GEN_OPTIONS}")
    print("=" * 60)

    ollama_available = True
    try:
        client.list()
    except Exception:
        ollama_available = False

    if not ollama_available:
        print("[X] 로컬 Ollama 서버에 연결할 수 없습니다. (로컬 PC에서 Ollama를 실행한 뒤 다시 시도하세요)")
        return

    doc_files = find_doc_files()
    needed = {"DOC-A", "DOC-B"}
    missing = needed - set(doc_files.keys())
    if missing:
        print(f"[안내] readfiles 폴더에 다음 문서가 없습니다: {', '.join(sorted(missing))}")
        print(f"       (DOC-A.md, DOC-B.pdf 처럼 'DOC-A'/'DOC-B'로 시작하는 파일명이어야 합니다)")
        print("       Q1처럼 문서가 필요 없는 질문만 진행합니다.")

    doc_texts = load_doc_texts(doc_files)
    print(f"\n[문서 로드 완료] {list(doc_texts.keys())}")

    for q in QUESTIONS:
        # 이 질문에 필요한 문서가 없으면 건너뜀 (Q1처럼 sources가 빈 경우는 통과)
        required = set(q["sources"])
        if required and not required.issubset(doc_texts.keys()):
            print(f"\n[건너뜀] {q['id']}: 필요한 문서({required})가 준비되지 않았습니다.")
            continue

        prompt = build_prompt(q, doc_texts)

        print(f"\n{'#'*60}")
        print(f"[{q['id']} | {q['type']}] sources={q['sources']}")
        print(f"질문: {q['question']}")

        for model in MODELS:
            print(f"\n{'='*50}")
            print(f"[모델: {model}] {q['id']} 질문을 보냈습니다. 기다려 주세요.")

            record = {
                "timestamp": now_str(),
                "question_id": q["id"],
                "question_type": q["type"],
                "sources": q["sources"],
                "question_text": q["question"],
                "note": q["note"],
                "model": model,
                "prompt_char_count": len(prompt),
                "settings": GEN_OPTIONS,
                "env_info": env_info,
            }

            start = time.time()
            try:
                response = client.chat(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    stream=False,
                    options=GEN_OPTIONS,
                )
                elapsed = time.time() - start

                # 응답 직후 현재 Ollama 모델의 VRAM 사용량 확인
                model_vram = get_ollama_model_vram(model)

                record["status"] = "성공"
                record["elapsed_sec"] = round(elapsed, 2)
                record["response"] = response.message.content
                record["eval_count"] = getattr(response, "eval_count", None)
                record["eval_duration_ns"] = getattr(response, "eval_duration", None)
                record["load_duration_ns"] = getattr(response, "load_duration", None)
                record["ollama_model_vram"] = model_vram

                print(f"[응답 시간] {elapsed:.2f}초")
                print("[답변]")
                print(response.message.content)

            except Exception as e:
                elapsed = time.time() - start
                record["status"] = "실패"
                record["elapsed_sec"] = round(elapsed, 2)
                record["error"] = str(e)
                print(f"[X] 오류 발생: {e}")

            save_result(record)

    print(f"\n{'='*60}")
    print(f"[완료] 결과가 '{RESULT_FILE}'에 저장되었습니다.")


if __name__ == "__main__":
    main()