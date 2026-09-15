import sys
import time
import platform
import subprocess
import json
from datetime import datetime

try:
    import ollama
    from ollama import Client
except ModuleNotFoundError:
    print("[U+26A0][U+FE0F] 'ollama' 패키지가 설치되어 있지 않습니다.")
    print("로컬 환경에서 다음 명령으로 설치 후 다시 실행해주세요: pip install ollama")
    raise SystemExit(1)

MODELS = [
    "exaone3.5:7.8b",
    "granite4.1:3b",
]
#QUESTION = "프롬프트 엔지니어링이 무엇인지 초보자에게 두 문장으로 설명해 주세요."
#QUESTION = "https://v.daum.net/v/20260914120153074   해당 뉴스 내용 요약좀"
QUESTION = "https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct  해당URL에 있는 Model Card를 참고해서 초보자에게 쉽게 이해할 수 있게 설명해주세요."

GEN_OPTIONS = {"temperature": 0, "num_predict": -1} # "num_predict": -1은 Ollama에서 모델이 허용하는 최대 토큰 수를 의미 (모델마다 다름)
RESULT_FILE = "log_01_ollama_chat.jsonl"

client = Client(host="http://127.0.0.1:11434", timeout=180)


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
    """DNS 조회로 인터넷 연결 가능 여부만 가볍게 확인합니다 (실제 웹 요청은 안 보냄)."""
    import socket
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


def print_environment_info(env_info):
    print("=" * 50)
    print("[실행 환경 기록]")
    for k, v in env_info.items():
        print(f"- {k:22s}: {v}")
    print(f"- 실행 대상 모델 태그   : {', '.join(MODELS)}")
    print(f"- 생성 설정(options)    : {GEN_OPTIONS}")
    print("=" * 50)


def save_result(record):
    """결과 한 건을 JSONL 파일에 한 줄씩 추가 저장합니다."""
    with open(RESULT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


env_info = get_env_info()
print_environment_info(env_info)

ollama_available = True
try:
    client.list()
except Exception:
    ollama_available = False

if not ollama_available:
    print("=" * 50)
    print("[X] 로컬 Ollama 서버에 연결할 수 없습니다.")
    print("이 스크립트는 Ollama가 설치된 본인 PC(로컬 환경)에서만 실행 가능합니다.")
    print("Google Colab 등 원격 환경에서는 실행할 수 없습니다.")
    print("=" * 50)

    save_result({
        "timestamp": datetime.now().isoformat(),
        "model": None,
        "status": "실패",
        "error": "로컬 Ollama 서버 연결 불가 (원격/미설치 환경으로 추정)",
        "env_info": env_info,
    })
else:
    for model in MODELS:
        print(f"\n{'='*50}")
        print(f"[모델: {model}] 질문을 보냈습니다. 답변을 기다려 주세요.")

        record = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "question": QUESTION,
            "settings": GEN_OPTIONS,
            "env_info": env_info,
        }

        start = time.time()
        try:
            response = client.chat(
                model=model,
                messages=[{"role": "user", "content": QUESTION}],
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
            print(f"[Ollama 답변]")
            print(response.message.content)

        except Exception as e:
            elapsed = time.time() - start
            record["status"] = "실패"
            record["elapsed_sec"] = round(elapsed, 2)
            record["error"] = str(e)

            print(f"[X] 오류 발생: {e}")
            print("모델 미설치, Ollama 미실행, 경로 문제 등을 확인하세요.")

        save_result(record)

    # 저장한 파일을 다시 열어 기록이 맞는지 확인
    # (줄 단위가 아니라 JSON 객체 경계를 직접 찾는 방식이라,
    #  파일이 한 줄짜리 JSONL이든 들여쓰기된 형태든 상관없이 안전하게 읽힘)
    print(f"\n{'='*50}")
    print(f"[저장 확인] {RESULT_FILE} 내용:")
    with open(RESULT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    decoder = json.JSONDecoder()
    pos = 0
    n = len(content)
    parsed_count = 0
    while pos < n:
        while pos < n and content[pos] in " \t\r\n":
            pos += 1
        if pos >= n:
            break
        try:
            row, end = decoder.raw_decode(content, pos)
        except json.JSONDecodeError as e:
            print(f"  [경고] 이 지점부터 파싱 실패, 이후 내용은 건너뜁니다: {e}")
            break
        ts = row.get("timestamp")
        mdl = row.get("model")
        st = row.get("status")
        print(f"- {ts} | {mdl} | {st}")
        parsed_count += 1
        pos = end
    print(f"[총 {parsed_count}건 확인됨]")