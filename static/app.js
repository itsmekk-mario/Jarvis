const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const core = document.querySelector("#talkButton");
const statusDot = document.querySelector("#statusDot");
const statusText = document.querySelector("#statusText");
const userText = document.querySelector("#userText");
const jarvisText = document.querySelector("#jarvisText");
const form = document.querySelector("#commandForm");
const input = document.querySelector("#commandInput");

let recognition;
let awaitingCommand = false;
let listening = false;

function setStatus(text, busy = false) {
  statusText.textContent = text;
  statusDot.classList.toggle("busy", busy);
}

function setListening(active) {
  listening = active;
  core.classList.toggle("listening", active);
}

function setSpeaking(active) {
  core.classList.toggle("speaking", active);
}

async function askJarvis(text) {
  const command = text.trim();
  if (!command) return;

  userText.textContent = command;
  jarvisText.textContent = "처리 중입니다.";
  setStatus("명령 처리 중", true);

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: command }),
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || "요청 처리에 실패했습니다.");
    }

    const payload = await response.json();
    jarvisText.textContent = payload.answer;
    speak(payload.answer);
  } catch (error) {
    const message = `오류가 발생했습니다. ${error.message}`;
    jarvisText.textContent = message;
    speak(message);
  }
}

function speak(text) {
  if (!window.speechSynthesis) {
    setStatus("음성 합성을 지원하지 않는 브라우저입니다");
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "ko-KR";
  utterance.rate = 0.98;
  utterance.pitch = 0.92;

  utterance.onstart = () => {
    setSpeaking(true);
    setStatus("Jarvis 응답 중", true);
  };
  utterance.onend = () => {
    setSpeaking(false);
    setStatus("대기 중");
  };
  utterance.onerror = () => {
    setSpeaking(false);
    setStatus("대기 중");
  };

  window.speechSynthesis.speak(utterance);
}

function setupRecognition() {
  if (!SpeechRecognition) {
    setStatus("브라우저 음성 인식 미지원");
    return;
  }

  recognition = new SpeechRecognition();
  recognition.lang = "ko-KR";
  recognition.continuous = true;
  recognition.interimResults = false;

  recognition.onstart = () => {
    setListening(true);
    setStatus('Wake word 대기 중: "자비스"');
  };

  recognition.onresult = (event) => {
    const result = event.results[event.results.length - 1][0].transcript.trim();
    const compact = result.replace(/\s/g, "");
    userText.textContent = result;

    if (awaitingCommand) {
      awaitingCommand = false;
      askJarvis(result);
      return;
    }

    if (compact.includes("자비스")) {
      awaitingCommand = true;
      speak("네, 듣고 있습니다.");
      setStatus("명령을 말씀하세요", true);
    }
  };

  recognition.onerror = (event) => {
    setListening(false);
    setStatus(`음성 인식 오류: ${event.error}`);
  };

  recognition.onend = () => {
    setListening(false);
    if (!window.speechSynthesis.speaking) {
      setTimeout(() => recognition.start(), 600);
    }
  };

  recognition.start();
}

core.addEventListener("click", () => {
  awaitingCommand = true;
  speak("네, 듣고 있습니다.");
  setStatus("명령을 말씀하세요", true);
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  askJarvis(input.value);
  input.value = "";
});

setupRecognition();
