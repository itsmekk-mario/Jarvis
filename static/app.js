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

function getWakeGreeting() {
  const hour = new Date().getHours();

  if (hour < 5) return "늦은 시간입니다. 무엇을 도와드릴까요?";
  if (hour < 12) return "좋은 아침입니다. 무엇을 도와드릴까요?";
  if (hour < 18) return "좋은 오후입니다. 무엇을 도와드릴까요?";
  return "좋은 저녁입니다. 무엇을 도와드릴까요?";
}

function beginCommandPrompt() {
  awaitingCommand = true;
  speak(getWakeGreeting(), () => setStatus("명령을 말씀하세요", true));
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

function speak(text, onDone) {
  if (!window.speechSynthesis) {
    setStatus("음성 합성을 지원하지 않는 브라우저입니다");
    if (onDone) onDone();
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
    if (onDone) {
      onDone();
    } else {
      setStatus("대기 중");
    }
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
      beginCommandPrompt();
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
  beginCommandPrompt();
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

function drawArc(cx, cy, radius, start, end, width, color) {
  coreContext.beginPath();
  coreContext.strokeStyle = color;
  coreContext.lineWidth = width;
  coreContext.arc(cx, cy, radius, start, end);
  coreContext.stroke();
}

function drawTickRing(cx, cy, radius, count, length, alpha, rotation = 0) {
  coreContext.save();
  coreContext.translate(cx, cy);
  coreContext.rotate(rotation);
  coreContext.strokeStyle = `rgba(127, 246, 255, ${alpha})`;
  coreContext.lineWidth = 1;

  for (let i = 0; i < count; i += 1) {
    const angle = (i / count) * Math.PI * 2;
    const major = i % 5 === 0;
    const tickLength = major ? length * 1.7 : length;
    const inner = radius - tickLength;
    const x1 = Math.cos(angle) * inner;
    const y1 = Math.sin(angle) * inner;
    const x2 = Math.cos(angle) * radius;
    const y2 = Math.sin(angle) * radius;
    coreContext.beginPath();
    coreContext.moveTo(x1, y1);
    coreContext.lineTo(x2, y2);
    coreContext.stroke();
  }

  coreContext.restore();
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
  const base = Math.min(width, height) * 0.39;
  const t = time * 0.001;

  coreContext.clearRect(0, 0, width, height);
  coreContext.globalCompositeOperation = "lighter";

  const stateEnergy = speaking ? 1 : processing ? 0.72 : listening ? 0.5 : 0.18;
  const outer = base * 1.08;
  const mid = base * 0.78;
  const inner = base * 0.43;
  const sweep = t * (0.46 + stateEnergy * 0.42);

  drawArc(cx, cy, outer, sweep, sweep + Math.PI * 1.55, 2.4, "rgba(127, 246, 255, 0.72)");
  drawArc(cx, cy, outer * 0.93, -sweep * 0.74, -sweep * 0.74 + Math.PI * 1.25, 1.2, "rgba(73, 189, 242, 0.44)");
  drawArc(cx, cy, mid, sweep * -1.25, sweep * -1.25 + Math.PI * 1.86, 3.2, "rgba(127, 246, 255, 0.52)");
  drawArc(cx, cy, inner, sweep * 1.6, sweep * 1.6 + Math.PI * 1.66, 2.4, "rgba(239, 255, 255, 0.34)");
  drawArc(cx, cy, mid * 1.03, Math.PI * 0.72, Math.PI * 0.92, 5.2, "rgba(255, 207, 66, 0.78)");

  drawTickRing(cx, cy, outer * 0.99, 96, base * 0.045, 0.52, sweep * 0.24);
  drawTickRing(cx, cy, mid * 1.05, 68, base * 0.032, 0.34, -sweep * 0.34);

  coreContext.strokeStyle = "rgba(127, 246, 255, 0.16)";
  coreContext.lineWidth = 1;
  for (let i = 0; i < 4; i += 1) {
    const offset = (i - 1.5) * base * 0.16;
    coreContext.beginPath();
    coreContext.moveTo(cx - base * 0.54, cy + offset);
    coreContext.lineTo(cx + base * 0.54, cy + offset);
    coreContext.stroke();
  }

  const tilt = -0.72 + Math.sin(t * 0.55) * 0.06;
  const cosTilt = Math.cos(tilt);
  const sinTilt = Math.sin(tilt);
  const rotation = t * (0.42 + stateEnergy * 0.52);
  const waveSpeed = speaking ? 9.5 : processing ? 6.8 : listening ? 4.8 : 2.4;
  const waveAmp = base * (0.006 + stateEnergy * 0.05);

  for (let ring = 0; ring < 4; ring += 1) {
    const ringRatio = 0.36 + ring * 0.135;
    const dots = 58 + ring * 18;
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
      const depthAlpha = Math.max(0.14, Math.min(0.75, 0.28 + projected.scale * 0.36));
      const pulseAlpha = depthAlpha * (0.45 + stateEnergy * 0.28);
      const dotRadius = (0.8 + ring * 0.08 + stateEnergy * 0.38) * projected.scale;

      drawDot(projected.x, projected.y, dotRadius, pulseAlpha, color);
    }
  }

  const centerDots = speaking ? 36 : processing ? 30 : listening ? 24 : 18;
  for (let i = 0; i < centerDots; i += 1) {
    const angle = (i / centerDots) * Math.PI * 2 - rotation * 1.4;
    const radius = base * (0.13 + Math.sin(t * 2.2 + i) * 0.018 + stateEnergy * 0.055);
    const x = cx + Math.cos(angle) * radius;
    const y = cy + Math.sin(angle) * radius * 0.42;
    drawDot(x, y, 1.55 + stateEnergy * 0.9, 0.55 + stateEnergy * 0.35, "rgba(238, 252, 255, ALPHA)");
  }

  const scannerAngle = t * 1.2;
  coreContext.strokeStyle = "rgba(127, 246, 255, 0.36)";
  coreContext.lineWidth = 1;
  coreContext.beginPath();
  coreContext.moveTo(cx, cy);
  coreContext.lineTo(cx + Math.cos(scannerAngle) * outer * 0.9, cy + Math.sin(scannerAngle) * outer * 0.9);
  coreContext.stroke();

  coreContext.globalCompositeOperation = "source-over";
  requestAnimationFrame(drawDottedCore);
}

resizeCoreCanvas();
window.addEventListener("resize", resizeCoreCanvas);
requestAnimationFrame(drawDottedCore);
