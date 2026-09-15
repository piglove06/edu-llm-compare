"""
readfiles 폴더 안의 md/txt/pdf 문서를 읽어서,
같은 질문을 여러 모델에 던지고 응답을 비교/저장하는 스크립트.

사용법:
1. 이 파일과 같은 위치에 readfiles/ 폴더를 만들고, 그 안에 .md, .txt, .pdf 파일을 넣는다.
2. QUESTION 변수에 문서 관련 질문을 적는다 (문서 내용은 자동으로 프롬프트에 합쳐짐).
3. 실행하면 각 파일 x 각 모델 조합으로 결과가 저장된다.
"""

import sys
import time
import platform
import subprocess
import json
import socket
from pathlib import Path
from datetime import datetime

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

# 문서 내용 뒤에 붙일 질문. {document} 자리에 파일 내용이 자동으로 채워짐.
QUESTION_TEMPLATE = (
    "다음은 문서 내용입니다.\n"
    "----- 문서 시작 -----\n"
    "{document}\n"
    "----- 문서 끝 -----\n\n"
    "위 문서 내용을 참고해서, 초보자도 이해하기 쉽게 핵심을 3~4문장으로 설명해 주세요. "
    "문서에 없는 내용은 지어내지 말고, 모르면 모른다고 답해 주세요."
)

GEN_OPTIONS = {"temperature": 0, "num_predict": 1024}

client = Client(host="http://127.0.0.1:11434", timeout=180)


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


def collect_readfiles() -> list[Path]:
    if not READFILES_DIR.exists():
        READFILES_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[안내] '{READFILES_DIR}' 폴더를 새로 만들었습니다. 여기에 md/txt/pdf 파일을 넣고 다시 실행하세요.")
        return []

    files = [
        p for p in READFILES_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in (".md", ".txt", ".pdf")
    ]
    return sorted(files)


# ------------------------------------------------------------------
# 환경 정보
# ------------------------------------------------------------------
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

    files = collect_readfiles()
    if not files:
        print(f"[안내] '{READFILES_DIR}' 폴더에 md/txt/pdf 파일이 없습니다. 파일을 넣고 다시 실행하세요.")
        return

    print(f"\n[문서 {len(files)}개 발견]")
    for f in files:
        print(f"  - {f.name}")

    for file_path in files:
        print(f"\n{'#'*60}")
        print(f"[문서: {file_path.name}]")

        try:
            document_text = read_document(file_path)
        except Exception as e:
            print(f"[X] 문서 읽기 실패: {e}")
            save_result({
                "timestamp": datetime.now().isoformat(),
                "source_file": file_path.name,
                "model": None,
                "status": "실패",
                "error": f"문서 읽기 실패: {e}",
                "env_info": env_info,
            })
            continue

        if not document_text.strip():
            print("[경고] 문서 내용이 비어 있습니다. 건너뜁니다.")
            continue

        question = QUESTION_TEMPLATE.format(document=document_text)

        for model in MODELS:
            print(f"\n{'='*50}")
            print(f"[모델: {model}] 문서 '{file_path.name}' 관련 질문을 보냈습니다. 기다려 주세요.")

            record = {
                "timestamp": datetime.now().isoformat(),
                "source_file": file_path.name,
                "model": model,
                "question_template": QUESTION_TEMPLATE,
                "document_char_count": len(document_text),
                "settings": GEN_OPTIONS,
                "env_info": env_info,
            }

            start = time.time()
            try:
                response = client.chat(
                    model=model,
                    messages=[{"role": "user", "content": question}],
                    stream=False,
                    options=GEN_OPTIONS,
                )
                elapsed = time.time() - start

                record["status"] = "성공"
                record["elapsed_sec"] = round(elapsed, 2)
                record["response"] = response.message.content
                record["eval_count"] = getattr(response, "eval_count", None)
                record["eval_duration_ns"] = getattr(response, "eval_duration", None)
                record["load_duration_ns"] = getattr(response, "load_duration", None)

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
