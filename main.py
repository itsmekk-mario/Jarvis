from __future__ import annotations

from actions import JarvisActions
from brain import JarvisBrain, OllamaError
from memory import ScheduleMemory
from utils import print_box, safe_json_dumps


EXIT_WORDS = {"exit", "quit", "q", "종료", "그만", "끝"}


def main() -> None:
    brain = JarvisBrain()
    memory = ScheduleMemory()
    actions = JarvisActions(brain=brain, memory=memory)

    print("Jarvis 로컬 AI 비서가 시작되었습니다.")
    print(f"Ollama 모델: {brain.model}")
    print("종료하려면 '종료' 또는 'exit'를 입력하세요.\n")

    while True:
        try:
            user_text = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nJarvis를 종료합니다.")
            break

        if not user_text:
            continue
        if user_text.lower() in EXIT_WORDS:
            print("Jarvis를 종료합니다.")
            break

        try:
            intent = brain.analyze_intent(user_text)
            print_box("Intent", safe_json_dumps({"intent": intent.intent, "content": intent.content}))

            result = actions.run(intent.intent, intent.content)
            print_box(result.title, result.content)
        except OllamaError as exc:
            print_box("Ollama 오류", str(exc))
        except Exception as exc:
            print_box("오류", f"처리 중 예상치 못한 오류가 발생했습니다: {exc}")


if __name__ == "__main__":
    main()
