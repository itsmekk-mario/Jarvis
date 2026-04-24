const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const core = document.querySelector("#talkButton");
const statusDot = document.querySelector("#statusDot");
const statusText = document.querySelector("#statusText");
const userText = document.querySelector("#userText");
const jarvisText = document.querySelector("#jarvisText");
const form = document.querySelector("#commandForm");
const input = document.querySelector("#commandInput");
const coreCanvas = document.querySelector("#coreCanvas");
const coreContext = coreCanvas.getContext("2d");

let recognition;
let awaitingCommand = false;
let listening = false;
let speaking = false;
let processing = false;

function setStatus(text, busy = false) {
  statusText.textContent = text;
  statusDot.classList.toggle("busy", busy);
}

function setListening(active) {
  listening = active;
  core.classList.toggle("listening", active);
}

function setSpeaking(active) {
  speaking = active;
  core.classList.toggle("speaking", active);
}

async function askJarvis(text) {
  const command = text.trim();
  if (!command) return;

  userText.textContent = command;
  jarvisText.textContent = "처리 중입니다.";
  processing = true;
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
    processing = false;
    speak(payload.answer);
  } catch (error) {
    const message = `오류가 발생했습니다. ${error.message}`;
    jarvisText.textContent = message;
    processing = false;
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

function resizeCoreCanvas() {
  const rect = coreCanvas.getBoundingClientRect();
  const scale = window.devicePixelRatio || 1;
  coreCanvas.width = Math.floor(rect.width * scale);
  coreCanvas.height = Math.floor(rect.height * scale);
  coreContext.setTransform(scale, 0, 0, scale, 0, 0);
}

function drawDot(x, y, radius, alpha, color) {
  coreContext.beginPath();
  coreContext.fillStyle = color.replace("ALPHA", alpha.toFixed(3));
  coreContext.arc(x, y, radius, 0, Math.PI * 2);
  coreContext.fill();
}

function projectPoint(x, y, z, cx, cy, perspective) {
  const depth = perspective / (perspective + z);
  return {
    x: cx + x * depth,
    y: cy + y * depth,
    scale: depth,
  };
}

function drawDottedCore(time) {
  const width = coreCanvas.clientWidth;
  const height = coreCanvas.clientHeight;
  const cx = width / 2;
  const cy = height / 2;
  const base = Math.min(width, height) * 0.34;
  const t = time * 0.001;

  coreContext.clearRect(0, 0, width, height);
  coreContext.globalCompositeOperation = "lighter";

  const stateEnergy = speaking ? 1 : processing ? 0.72 : listening ? 0.5 : 0.18;
  const tilt = -0.72 + Math.sin(t * 0.55) * 0.06;
  const cosTilt = Math.cos(tilt);
  const sinTilt = Math.sin(tilt);
  const rotation = t * (0.42 + stateEnergy * 0.52);
  const waveSpeed = speaking ? 9.5 : processing ? 6.8 : listening ? 4.8 : 2.4;
  const waveAmp = base * (0.015 + stateEnergy * 0.12);

  for (let ring = 0; ring < 5; ring += 1) {
    const ringRatio = 0.42 + ring * 0.155;
    const dots = 74 + ring * 20;
    const ringPhase = rotation * (ring % 2 === 0 ? 1 : -0.7) + ring * 0.8;
    const color =
      ring % 3 === 0
        ? "rgba(110, 234, 255, ALPHA)"
        : ring % 3 === 1
          ? "rgba(128, 255, 216, ALPHA)"
          : "rgba(157, 140, 255, ALPHA)";

    for (let i = 0; i < dots; i += 1) {
      const angle = (i / dots) * Math.PI * 2 + ringPhase;
      const algorithmicNoise =
        Math.sin(angle * (3 + ring) + t * waveSpeed) *
        Math.cos(angle * 2 - t * (1.7 + ring * 0.2));
      const morph = waveAmp * algorithmicNoise;
      const radius = base * ringRatio + morph;
      const localX = Math.cos(angle) * radius;
      const localY = Math.sin(angle) * radius;
      const y3d = localY * cosTilt;
      const z3d = localY * sinTilt + Math.sin(angle * 2 + t) * base * 0.06;
      const projected = projectPoint(localX, y3d, z3d, cx, cy, base * 3.2);
      const depthAlpha = Math.max(0.18, Math.min(0.92, 0.42 + projected.scale * 0.42));
      const pulseAlpha = depthAlpha * (0.58 + stateEnergy * 0.36);
      const dotRadius = (1.05 + ring * 0.08 + stateEnergy * 0.55) * projected.scale;

      drawDot(projected.x, projected.y, dotRadius, pulseAlpha, color);
    }
  }

  const centerDots = speaking ? 42 : processing ? 34 : listening ? 28 : 22;
  for (let i = 0; i < centerDots; i += 1) {
    const angle = (i / centerDots) * Math.PI * 2 - rotation * 1.4;
    const radius = base * (0.13 + Math.sin(t * 2.2 + i) * 0.018 + stateEnergy * 0.055);
    const x = cx + Math.cos(angle) * radius;
    const y = cy + Math.sin(angle) * radius * 0.42;
    drawDot(x, y, 1.55 + stateEnergy * 0.9, 0.55 + stateEnergy * 0.35, "rgba(238, 252, 255, ALPHA)");
  }

  coreContext.globalCompositeOperation = "source-over";
  requestAnimationFrame(drawDottedCore);
}

resizeCoreCanvas();
window.addEventListener("resize", resizeCoreCanvas);
requestAnimationFrame(drawDottedCore);
