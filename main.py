from dotenv import load_dotenv

from brain import JarvisBrain
from tts import Speaker
from voice import VoiceInput


EXIT_WORDS = {"종료", "그만", "꺼져", "멈춰", "끝내"}


def main() -> None:
    load_dotenv()

    voice = VoiceInput(wake_word="자비스")
    brain = JarvisBrain()
    speaker = Speaker()

    speaker.say("자비스가 준비되었습니다.")

    while True:
        voice.wait_for_wake_word()
        speaker.say("네, 듣고 있습니다.")

        command = voice.listen_command()
        if not command:
            speaker.say("명령을 잘 듣지 못했습니다. 다시 불러 주세요.")
            continue

        print(f"명령: {command}")
        normalized = command.replace(" ", "")
        if any(word in normalized for word in EXIT_WORDS):
            speaker.say("자비스를 종료합니다.")
            break

        answer = brain.ask(command)
        speaker.say(answer)


if __name__ == "__main__":
    main()
