"use strict";
(() => {
  if (document.querySelector(".start-devil")) return;
  const mascot = document.createElement("aside");
  mascot.className = "start-devil";
  mascot.setAttribute("aria-label", "Kleiner Würfelteufel");
  mascot.innerHTML = `
    <style>
      .start-devil{position:fixed;left:max(8px,env(safe-area-inset-left));bottom:calc(8px + env(safe-area-inset-bottom));width:120px;z-index:25;text-align:center;font:13px system-ui;color:#ffe9b8}
      .start-devil .devil-roll-button{display:block;width:120px;height:132px;padding:0;border:0;background:none;box-shadow:none;border-radius:24px;touch-action:manipulation}
      .start-devil button:hover,.start-devil button:active{background:none;box-shadow:none;transform:none}
      .start-devil button:focus-visible{outline:2px solid #ffe3a3;outline-offset:2px}
      .start-devil svg{display:block;width:100%;height:100%;overflow:visible;filter:drop-shadow(0 4px 5px #0008)}
      .start-devil output{display:block;min-height:22px;padding:3px 7px;border:1px solid #b38d5680;border-radius:12px;background:#201612eb;text-shadow:0 1px 2px #000}
      .devil-float{animation:devil-bob 4s ease-in-out infinite}
      .devil-tail{transform-origin:116px 125px;animation:devil-tail 3s ease-in-out infinite alternate}
      .devil-eye{transform-box:fill-box;transform-origin:center;animation:devil-blink 6s linear infinite}
      .start-devil.rolling .devil-die{transform-box:fill-box;transform-origin:center;animation:devil-roll .9s ease-in-out}
      @keyframes devil-bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}
      @keyframes devil-tail{from{transform:rotate(-5deg)}to{transform:rotate(6deg)}}
      @keyframes devil-blink{0%,43%,47%,100%{transform:scaleY(1)}45%{transform:scaleY(.12)}}
      @keyframes devil-roll{0%{transform:translateY(0) rotate(0)}45%{transform:translateY(-35px) rotate(190deg)}75%{transform:translateY(-5px) rotate(340deg)}100%{transform:translateY(0) rotate(360deg)}}
      @media(max-width:600px){.start-devil{width:88px;font-size:11px}.start-devil .devil-roll-button{width:88px;height:98px}}
      @media print{.start-devil{display:none}}
    </style>
    <button class="devil-roll-button" type="button" title="Klick mich: W20 würfeln" aria-label="Mit dem kleinen Teufel einen W20 würfeln">
      <svg viewBox="0 0 160 170" aria-hidden="true" focusable="false">
        <defs><linearGradient id="devil-red" x2="0" y2="1"><stop stop-color="#ed705d"/><stop offset="1" stop-color="#ac3438"/></linearGradient>
        <linearGradient id="devil-gold" x2="1" y2="1"><stop stop-color="#fff0af"/><stop offset="1" stop-color="#cf8a35"/></linearGradient></defs>
        <ellipse cx="78" cy="157" rx="45" ry="7" fill="#000" opacity=".25"/>
        <g class="devil-float">
          <path class="devil-tail" d="M112 128 Q157 145 146 108 L140 112 L147 94 L157 109 L151 108 Q164 153 114 141" fill="#bc4241" stroke="#6e282f" stroke-width="2"/>
          <path d="M48 97 Q17 79 15 111 Q32 102 32 124 L54 120 M109 97 Q141 79 143 111 Q124 102 125 125 L105 120" fill="#8f3542" stroke="#602735" stroke-width="2"/>
          <ellipse cx="79" cy="126" rx="32" ry="29" fill="url(#devil-red)" stroke="#7c3032" stroke-width="2"/>
          <ellipse cx="61" cy="151" rx="16" ry="8" fill="#b9403d"/><ellipse cx="99" cy="151" rx="16" ry="8" fill="#b9403d"/>
          <path d="M45 47 Q28 42 33 16 Q42 31 57 34 M103 34 Q119 31 128 16 Q133 42 116 48" fill="#ffdfa0" stroke="#a96e49" stroke-width="2"/>
          <path d="M45 54 Q24 40 27 65 L44 77 M116 54 Q136 40 132 65 L117 77" fill="#d95b52"/>
          <path d="M40 64 Q35 29 80 29 Q126 29 121 65 Q128 102 80 108 Q32 103 40 64" fill="url(#devil-red)" stroke="#7c3032" stroke-width="2"/>
          <path d="M66 32 Q81 15 91 32" fill="#df5a4f"/>
          <ellipse class="devil-eye" cx="61" cy="66" rx="9" ry="12" fill="#33252b"/><ellipse class="devil-eye" cx="99" cy="66" rx="9" ry="12" fill="#33252b"/>
          <circle cx="64" cy="62" r="3" fill="white"/><circle cx="102" cy="62" r="3" fill="white"/>
          <ellipse cx="48" cy="81" rx="8" ry="4" fill="#ff9b87" opacity=".7"/><ellipse cx="112" cy="81" rx="8" ry="4" fill="#ff9b87" opacity=".7"/>
          <path d="M66 85 Q80 99 94 85" fill="#79343b" stroke="#79343b" stroke-width="2" stroke-linecap="round"/>
          <path d="M69 87 L73 93 L77 90 M84 90 L88 93 L92 87" fill="#fff4d2"/>
          <g class="devil-die"><path d="M80 94 L108 110 L108 137 L80 153 L52 137 L52 110 Z" fill="url(#devil-gold)" stroke="#704824" stroke-width="2"/>
            <path d="M80 94 L64 132 L96 132 Z M52 110 L64 132 L52 137 M108 110 L96 132 L108 137 M64 132 L80 153 L96 132" fill="none" stroke="#9f6a30" stroke-width="1.5"/>
            <text class="devil-number" x="80" y="126" text-anchor="middle" fill="#50341e" font-family="Georgia,serif" font-size="19" font-weight="bold">20</text></g>
          <ellipse cx="48" cy="119" rx="9" ry="12" fill="#df6355" stroke="#8f3638"/><ellipse cx="112" cy="119" rx="9" ry="12" fill="#df6355" stroke="#8f3638"/>
        </g>
      </svg>
    </button><output aria-live="polite" aria-atomic="true">W20 würfeln</output>`;
  document.body.append(mascot);
  const button = mascot.querySelector("button");
  const number = mascot.querySelector(".devil-number");
  const output = mascot.querySelector("output");
  const roll = () => {
    const random = new Uint32Array(1);
    const limit = Math.floor(0x100000000 / 20) * 20;
    do { crypto.getRandomValues(random); } while (random[0] >= limit);
    return random[0] % 20 + 1;
  };
  button.addEventListener("click", () => {
    if (button.disabled) return;
    button.disabled = true;
    const result = roll();
    number.textContent = "?";
    output.textContent = "Würfelt …";
    mascot.classList.add("rolling");
    window.setTimeout(() => {
      mascot.classList.remove("rolling");
      number.textContent = String(result);
      output.textContent = result === 20 ? "W20: 20 ✦" : result === 1 ? "W20: 1 …" : "W20: " + result;
      button.disabled = false;
    }, 900);
  });
})();
