// comunicar com o backend Python do simulador

// CONFIG (possivel troca de rotas se necessário) 
const API_URL = "http://127.0.0.1:5000";
const API_LOAD  = "/load";
const API_RUN   = "/run";
const API_STEP  = "/step";
const API_RESET = "/reset";
const API_DUMP  = "/dump";


// ELEMENTOS DA UI 
const editor       = document.getElementById("editor");
const consoleBox   = document.getElementById("console");
const registersDiv = document.getElementById("registers");
const memoryDiv    = document.getElementById("memory");

const loadBtn  = document.getElementById("loadBtn");
const runBtn   = document.getElementById("runBtn");
const stepBtn  = document.getElementById("stepBtn");
const resetBtn = document.getElementById("resetBtn");
const dumpBtn  = document.getElementById("dumpBtn");

// INPUTS DE SEGMENTO
const inputCS = document.getElementById("seg-cs");
const inputDS = document.getElementById("seg-ds");
const inputSS = document.getElementById("seg-ss");
const inputES = document.getElementById("seg-es");

// Estado local mínimo para UI
let running = false;

// -------------------- helpers --------------------
function appendConsole(text, kind = "info") {
    // kind: info | error | log
    const p = document.createElement("p");
    p.textContent = text;
    p.className = `console-${kind}`;
    consoleBox.appendChild(p);
    consoleBox.scrollTop = consoleBox.scrollHeight;
}

function clearConsole() {
    consoleBox.innerHTML = "";
}

function setButtonsEnabled(enabled) {
    loadBtn.disabled  = !enabled;
    runBtn.disabled   = !enabled;
    stepBtn.disabled  = !enabled;
    resetBtn.disabled = !enabled;
    dumpBtn.disabled  = !enabled;
}

// Generic POST helper
async function apiPost(path, body = {}) {
    try {
        const res = await fetch(API_URL + path, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });

        const json = await res.json();

        if (!res.ok) {
            // Usa o objeto json já lido para pegar a mensagem de erro
            throw new Error(json.message || json.error || `Erro HTTP ${res.status}`);
        }
        
        // Retorna o objeto json já lido
        return json;
    } catch (err) {
        throw err;
    }
}

// Transformar memória retornada (bytes) em linhas para exibir
function formatMemoryView(memoryArray, opts = {}) {
    // memoryArray: array of bytes (0..255) OR array of words (0..65535)
    // opts.words: boolean para interpretar como words (cada índice é uma palavra)
    const lines = [];
    const maxLines = opts.maxLines || 256;

    if (!Array.isArray(memoryArray)) return ["<sem memória>"];

    if (opts.words) {
        for (let i = 0; i < Math.min(memoryArray.length, maxLines); i++) {
            lines.push(`[${i}] → ${memoryArray[i]}`);
        }
    } else {
        // Mostrar como bytes agrupados em palavras (duas em little-endian)
        const showWords = opts.wordGroup ?? true;
        if (!showWords) {
            for (let i = 0; i < Math.min(memoryArray.length, maxLines); i++) {
                lines.push(`[${i}] → ${memoryArray[i]}`);
            }
        } else {
            // agrupa por 2 bytes (little-endian) para exibir palavras
            const wordCount = Math.floor(memoryArray.length / 2);
            for (let i = 0; i < Math.min(wordCount, maxLines); i++) {
                const low = memoryArray[i * 2];
                const high = memoryArray[i * 2 + 1];
                const word = (high << 8) | low;
                lines.push(`[${i}] → ${word}`);
            }
        }
    }

    return lines;
}

// Recebe o 'state' retornado pelo servidor e atualiza a UI
function updateUI(state) {
    if (!state) return;

    // REGISTRADORES
    if (state.registers) {
        // mostra cada chave em ordem se possível
        const keys = Object.keys(state.registers);
        registersDiv.innerHTML = keys.map(k => `${k}: ${state.registers[k]}`).join("<br>");
    }

    // FLAGS + IP
    if (state.flags || typeof state.ip !== "undefined") {
        const fl = state.flags ? Object.entries(state.flags).map(([k,v]) => `${k}:${v}`).join(" ") : "";
        const ip  = (typeof state.ip !== "undefined") ? `IP: ${state.ip}` : "";
        // adiciona abaixo dos registradores (ou mistura se preferir)
        registersDiv.innerHTML += `<br>${ip} ${fl}`;
    }

    // MEMÓRIA
    if (state.memory) {
        // Detecta se memory veio como array de bytes
        // Mostramos default como palavras (2 bytes) para ficar parecido com sua interface original
        const memLines = formatMemoryView(state.memory, { wordGroup: true, maxLines: 128 });
        memoryDiv.innerHTML = memLines.join("<br>");
    }
}

// ações
async function loadProgram() {
    clearConsole();
    appendConsole("Enviando programa para o servidor...");
    try {
        const code = editor.value;
        const segments = {
            cs: inputCS.value || 0,
            ds: inputDS.value || 0,
            ss: inputSS.value || 0,
            es: inputES.value || 0
        };
        const res = await apiPost(API_LOAD, { code, segments });
        if (res.message) appendConsole(res.message);
        if (res.state) {
            updateUI(res.state);
            appendConsole("Programa carregado no backend.");
        } else {
            appendConsole("Programa carregado (sem estado retornado).");
        }
    } catch (err) {
        appendConsole("Erro ao carregar: " + err, "error");
    }
}

async function runProgram() {
    clearConsole();
    appendConsole("Executando programa (servidor)...");
    setButtonsEnabled(false);
    running = true;
    try {
        const res = await apiPost(API_RUN, {});
        // espera obter logs + state
        if (res.logs && Array.isArray(res.logs)) {
            res.logs.forEach(l => appendConsole(l));
        }
        if (res.state) updateUI(res.state);
        appendConsole("Execução finalizada.");
    } catch (err) {
        appendConsole("Erro ao executar: " + err, "error");
    } finally {
        running = false;
        setButtonsEnabled(true);
    }
}

async function stepProgram() {
    try {
        const res = await apiPost(API_STEP, {});
        if (res.logs && Array.isArray(res.logs)) res.logs.forEach(l => appendConsole(l));
        if (res.state) updateUI(res.state);
    } catch (err) {
        appendConsole("Erro no step: " + err, "error");
    }
}

async function resetProgram() {
    clearConsole();
    appendConsole("Solicitando reset ao servidor...");
    try {
        const res = await apiPost(API_RESET, {});
        if (res.message) appendConsole(res.message);
        if (res.state) updateUI(res.state);
    } catch (err) {
        appendConsole("Erro ao resetar: " + err, "error");
    }
}

async function dumpMemory() {
    appendConsole("Solicitando dump de memória...");
    try {
        const res = await apiPost(API_DUMP, {});
        if (res.message) appendConsole(res.message);
        if (res.memory && Array.isArray(res.memory)) {
            // mostra primeiro 128 words (ou 256 bytes)
            const lines = formatMemoryView(res.memory, { wordGroup: true, maxLines: 256 });
            lines.forEach(l => appendConsole(l));
        } else {
            appendConsole("Resposta de dump sem memória.");
        }
    } catch (err) {
        appendConsole("Erro ao pedir dump: " + err, "error");
    }
}

// ligações
loadBtn.onclick  = () => loadProgram();
runBtn.onclick   = () => runProgram();
stepBtn.onclick  = () => stepProgram();
resetBtn.onclick = () => resetProgram();
dumpBtn.onclick  = () => dumpMemory();

// Inicializa UI com estado vazio
registersDiv.innerHTML = "AX: 0<br>BX: 0<br>CX: 0<br>DX: 0<br>IP: 0<br>CS: 0<br>DS: 0<br>SS: 0<br>ES: 0";
memoryDiv.innerHTML = Array.from({length:32}).map((_,i) => `[${i}] → 0`).join("<br>");
