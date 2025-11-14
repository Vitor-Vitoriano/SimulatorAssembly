// Registradores simulados
let registers = {
    AX: 0,
    BX: 0,
    CX: 0,
    DX: 0,
    IP: 0
};

// Memória simples (tamanho 32 posições)
let memory = new Array(32).fill(0);

// Código carregado e linha atual
let program = [];
let currentLine = 0;

// ELEMENTOS DA INTERFACE
const editor = document.getElementById("editor");
const consoleBox = document.getElementById("console");
const registersDiv = document.getElementById("registers");
const memoryDiv = document.getElementById("memory");

// BOTÕES
document.getElementById("loadBtn").onclick = loadProgram;
document.getElementById("runBtn").onclick = runProgram;
document.getElementById("stepBtn").onclick = stepProgram;
document.getElementById("resetBtn").onclick = resetProgram;
document.getElementById("dumpBtn").onclick = dumpMemory;

// -------------------------------------------
// FUNÇÃO → Atualiza console
// -------------------------------------------
function logToConsole(msg) {
    consoleBox.innerHTML += "<br> " + msg;
    consoleBox.scrollTop = consoleBox.scrollHeight;
}

// -------------------------------------------
// FUNÇÃO → Atualiza painel de registradores
// -------------------------------------------
function updateRegisters() {
    registersDiv.innerHTML = `
        AX: ${registers.AX}<br>
        BX: ${registers.BX}<br>
        CX: ${registers.CX}<br>
        DX: ${registers.DX}<br>
        IP: ${registers.IP}
    `;
}

// -------------------------------------------
// FUNÇÃO → Atualiza painel da memória
// -------------------------------------------
function updateMemory() {
    memoryDiv.innerHTML = memory
        .map((v, i) => `[${i}] → ${v}`)
        .join("<br>");
}

// -------------------------------------------
// CARREGAR PROGRAMA
// -------------------------------------------
function loadProgram() {
    program = editor.value.split("\n").map(l => l.trim());
    currentLine = 0;
    registers.IP = 0;

    consoleBox.innerHTML = "> Programa carregado.";
    updateRegisters();
    updateMemory();
}

// -------------------------------------------
// EXECUTAR PROGRAMA INTEIRO
// -------------------------------------------
function runProgram() {
    consoleBox.innerHTML = "> Executando programa...";

    while (currentLine < program.length) {
        executeLine(program[currentLine]);
        currentLine++;
        registers.IP = currentLine;
    }

    logToConsole("Execução finalizada.");
    updateRegisters();
    updateMemory();
}

// -------------------------------------------
// EXECUTAR 1 LINHA (STEP)
// -------------------------------------------
function stepProgram() {
    if (currentLine >= program.length) {
        logToConsole("Fim do programa.");
        return;
    }

    const line = program[currentLine];
    logToConsole(`Executando: ${line}`);

    executeLine(line);

    currentLine++;
    registers.IP = currentLine;

    updateRegisters();
    updateMemory();
}

// -------------------------------------------
// RESETAR SIMULADOR
// -------------------------------------------
function resetProgram() {
    registers = { AX: 0, BX: 0, CX: 0, DX: 0, IP: 0 };
    memory.fill(0);
    currentLine = 0;

    consoleBox.innerHTML = "> Simulador resetado.";
    updateRegisters();
    updateMemory();
}

// -------------------------------------------
// DUMP DA MEMÓRIA (MOSTRAR NO CONSOLE)
// -------------------------------------------
function dumpMemory() {
    consoleBox.innerHTML += "<br><br><b>Dump da Memória:</b><br>";
    memory.forEach((v, i) => {
        consoleBox.innerHTML += `[${i}] → ${v}<br>`;
    });
}

// -------------------------------------------
// INTERPRETAR UMA LINHA (LINGUAGEM SIMPLIFICADA)
// -------------------------------------------
function executeLine(line) {
    if (!line || line.startsWith(";")) return;

    const parts = line.split(" ");
    const instr = parts[0].toUpperCase();

    switch (instr) {

        case "MOV":
            // MOV AX, 10
            let [reg, value] = parts[1].split(",");
            reg = reg.trim().toUpperCase();
            value = parseInt(value.trim());
            registers[reg] = value;
            break;

        case "ADD":
            // ADD AX, 5
            let [r1, v1] = parts[1].split(",");
            r1 = r1.trim().toUpperCase();
            v1 = parseInt(v1.trim());
            registers[r1] += v1;
            break;

        case "STORE":
            // STORE AX, 5
            let [r2, pos] = parts[1].split(",");
            r2 = r2.trim().toUpperCase();
            pos = parseInt(pos.trim());
            memory[pos] = registers[r2];
            break;

        case "LOAD":
            // LOAD BX, 2
            let [r3, pos2] = parts[1].split(",");
            r3 = r3.trim().toUpperCase();
            pos2 = parseInt(pos2.trim());
            registers[r3] = memory[pos2];
            break;

        default:
            logToConsole("Instrução desconhecida: " + instr);
    }
}
