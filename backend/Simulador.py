# -*- coding: utf-8 -*-
import sys
import re

class CPU:
    """
    Simula os registradores da CPU x86 16-bit (Modo Real).
    Implementa o acesso aos registradores de 8-bit (high/low) e flags básicas.
    """
    def __init__(self):
        # Dicionário interno para os registradores de 16-bit
        self._registers = {
            'ax': 0, 'bx': 0, 'cx': 0, 'dx': 0,
            'si': 0, 'di': 0, 'bp': 0xFFFE, 'sp': 0xFFFE, 'ip': 0,
            'cs': 0x0000, 'ds': 0x0000, 'ss': 0x0000, 'es': 0x0000
        }
        # Flags de status
        self.flags = {
            'ZF': 0, # Zero Flag
            'SF': 0, # Sign Flag
            'OF': 0, # Overflow Flag
            'CF': 0, # Carry Flag
        }

    def get_reg(self, reg_name):
        """Pega o valor de um registrador (16-bit ou 8-bit)"""
        reg = reg_name.lower()

        if reg in self._registers: return self._registers[reg]
        if reg == 'al': return self._registers['ax'] & 0xFF
        if reg == 'bl': return self._registers['bx'] & 0xFF
        if reg == 'cl': return self._registers['cx'] & 0xFF
        if reg == 'dl': return self._registers['dx'] & 0xFF
        if reg == 'ah': return (self._registers['ax'] >> 8) & 0xFF
        if reg == 'bh': return (self._registers['bx'] >> 8) & 0xFF
        if reg == 'ch': return (self._registers['cx'] >> 8) & 0xFF
        if reg == 'dh': return (self._registers['dx'] >> 8) & 0xFF

        raise ValueError(f"Registrador '{reg_name}' desconhecido")

    def set_reg(self, reg_name, value):
        """Define o valor de um registrador (16-bit ou 8-bit)"""
        reg = reg_name.lower()
        value = int(value)

        if reg in self._registers:
            self._registers[reg] = value & 0xFFFF
            return

        if reg == 'al': self._registers['ax'] = (self._registers['ax'] & 0xFF00) | (value & 0xFF); return
        if reg == 'bl': self._registers['bx'] = (self._registers['bx'] & 0xFF00) | (value & 0xFF); return
        if reg == 'cl': self._registers['cx'] = (self._registers['cx'] & 0xFF00) | (value & 0xFF); return
        if reg == 'dl': self._registers['dx'] = (self._registers['dx'] & 0xFF00) | (value & 0xFF); return
        if reg == 'ah': self._registers['ax'] = (self._registers['ax'] & 0x00FF) | ((value & 0xFF) << 8); return
        if reg == 'bh': self._registers['bx'] = (self._registers['bx'] & 0x00FF) | ((value & 0xFF) << 8); return
        if reg == 'ch': self._registers['cx'] = (self._registers['cx'] & 0x00FF) | ((value & 0xFF) << 8); return
        if reg == 'dh': self._registers['dx'] = (self._registers['dx'] & 0x00FF) | ((value & 0xFF) << 8); return

        raise ValueError(f"Registrador '{reg_name}' desconhecido")

    # -- Helpers para flags --
    def _to_signed(self, val, bits):
        mask = (1 << bits) - 1
        max_signed = (1 << (bits - 1)) - 1
        v = val & mask
        if v > max_signed:
            v -= (mask + 1)
        return v

    def set_flags_arith(self, result, bits=16):
        """Atualiza apenas ZF e SF (compatível com implementação anterior)."""
        mask = 0xFFFF if bits == 16 else 0xFF
        max_signed = 0x7FFF if bits == 16 else 0x7F

        result = result & mask
        signed_result = result

        # Converte para "signed" para checar o SF
        if signed_result > max_signed:
            signed_result -= (mask + 1)

        # ZF: Zero Flag
        self.flags['ZF'] = 1 if result == 0 else 0

        # SF: Sign Flag
        self.flags['SF'] = 1 if signed_result < 0 else 0

    def set_flags_full(self, val1, val2, result, op='add', bits=16, incdec_cf_unchanged=False):
        """
        Define ZF, SF, CF, OF para operações aritméticas.
        op: 'add' or 'sub'
        For INC/DEC, set incdec_cf_unchanged=True to leave CF untouched (x86 behavior).
        """
        mask = (1 << bits) - 1
        signbit = 1 << (bits - 1)

        v1 = val1 & mask
        v2 = val2 & mask
        res = result & (2 * mask + 1)  # keep full result for carry detection
        res_masked = result & mask

        # ZF
        self.flags['ZF'] = 1 if res_masked == 0 else 0
        # SF
        self.flags['SF'] = 1 if (res_masked & signbit) != 0 else 0

        # CF
        if op == 'add':
            self.flags['CF'] = 1 if (res > mask) else 0
            # OF: when sign of operands are the same and sign of result differs
            s1 = (v1 & signbit) != 0
            s2 = (v2 & signbit) != 0
            sr = (res_masked & signbit) != 0
            self.flags['OF'] = 1 if (s1 == s2 and s1 != sr) else 0
        elif op == 'sub':
            # In subtraction CF is set if a borrow was needed (unsigned v1 < v2)
            self.flags['CF'] = 1 if (v1 < v2) else 0
            # OF: if signs of v1 and v2 differ and sign of result differs from sign of v1
            s1 = (v1 & signbit) != 0
            s2 = (v2 & signbit) != 0
            sr = (res_masked & signbit) != 0
            self.flags['OF'] = 1 if (s1 != s2 and s1 != sr) else 0
        else:
            # For safety, clear CF/OF unless instructed otherwise
            if not incdec_cf_unchanged:
                self.flags['CF'] = 0
                self.flags['OF'] = 0

    def dump(self):
        """Exibe o estado atual dos registradores 16-bit como um dicionário"""
        register_state = {
            'ax': self._registers['ax'],
            'bx': self._registers['bx'],
            'cx': self._registers['cx'],
            'dx': self._registers['dx'],
            'si': self._registers['si'],
            'di': self._registers['di'],
            'bp': self._registers['bp'],
            'sp': self._registers['sp'],
            'ip': self._registers['ip'],
            'cs': self._registers['cs'],
            'ds': self._registers['ds'],
            'ss': self._registers['ss'],
            'es': self._registers['es']
        }

        # Junta os registradores e as flags
        return {
            "registers": register_state,
            "flags": self.flags
        }

    def reset(self):
        # Zera registradores mantendo sp/bp no topo
        for r in self._registers:
            self._registers[r] = 0
        # Reset correto das flags (mesmas keys usadas em todo o código)
        self.flags = {
            'ZF': 0,
            'SF': 0,
            'OF': 0,
            'CF': 0
        }
        # Reconfigura SP/BP para topo da pilha por convenção
        self._registers['sp'] = 0xFFFE
        self._registers['bp'] = 0xFFFE

class Simulator:
    """O Simulador principal com todas as instruções da A3."""

    def __init__(self, memory_size=1048576): # 1MB por padrão
        self.cpu = CPU()
        self.memory = bytearray(memory_size) # Memória byte-addressable
        self.program = {}
        self.labels = {}  # Dicionário para guardar rótulos (Labels)
        self.output_log = ""
        self.trace_hardware = False
        self.constants = {}  # Para apoiar diretivas CONST

        # Pilha começa no topo da memória
        self.cpu.set_reg('sp', 0xFFFE)
        self.cpu.set_reg('bp', 0xFFFE)

    def _is_reg_8bit(self, reg_name):
        """Checa se um nome de registrador é 8-bit"""
        return reg_name.lower() in ('al', 'ah', 'bl', 'bh', 'cl', 'ch', 'dl', 'dh')

    def _get_instruction_size(self, operands):
        # Mantido simples; pode ser aprimorado para encoder/decoder real
        size = 2  # (Opcode)
        size += len(operands) * 2 # Cada operando adiciona 2 bytes (estimativa)
        return size

    def log_hardware(self, system, msg):
        """Registra eventos de baixo nível se o trace estiver ativo"""
        if self.trace_hardware:
            self.output_log += f"   [{system}] {msg}\n"

    def get_physical_address(self, segment_reg, offset):
        """
        Calcula Endereço Físico = (Segmento * 16) + Offset
        """
        seg_val = self.cpu.get_reg(segment_reg)

        # Garante 16-bit unsigned para o offset
        offset = offset & 0xFFFF

        physical_addr = (seg_val << 4) + offset

        if self.trace_hardware:
            calc_str = f"({segment_reg.upper()}:{seg_val:04X} * 16) + {offset:04X} = {physical_addr:05X}"
            self.log_hardware("MMU", f"Calc Endereço: {calc_str}")

        # Wrap-around para simular comportamento x86
        if physical_addr >= len(self.memory):
            physical_addr %= len(self.memory)

        return physical_addr

    def _read_memory(self, offset, bits=16, segment='ds'):
        """Lê 8 ou 16 bits da memória (Little-Endian) com proteção contra overflow de índice"""
        address = self.get_physical_address(segment, offset)
        memlen = len(self.memory)

        if self.trace_hardware:
            self.log_hardware("BUS", f"Endereço {address:05X}h -> Barramento de Endereços")
            self.log_hardware("BUS", f"Sinal de Controle: MEMR (Ler Memória)")

        if bits == 8:
            return self.memory[address % memlen]

        # 16-bit: lê duas posições com wrap-around seguro
        low = self.memory[address % memlen]
        high = self.memory[(address + 1) % memlen]
        val = (high << 8) | low

        if self.trace_hardware:
            self.log_hardware("BUS", f"Dado {val:04X}h -> Barramento de Dados")

        return val

    def _write_memory(self, offset, value, bits=16, segment='ds'):
        """Escreve 8 ou 16 bits na memória (Little-Endian) com proteção contra overflow de índice"""
        address = self.get_physical_address(segment, offset)
        memlen = len(self.memory)

        if self.trace_hardware:
            self.log_hardware("BUS", f"Endereço {address:05X}h -> Barramento de Endereços")
            self.log_hardware("BUS", f"Dado {value:04X}h -> Barramento de Dados")
            self.log_hardware("BUS", f"Sinal de Controle: MEMW (Escrever Memória)")

        if bits == 8:
            self.memory[address % memlen] = value & 0xFF
            return

        val_low = value & 0xFF
        val_high = (value >> 8) & 0xFF
        self.memory[address % memlen] = val_low
        self.memory[(address + 1) % memlen] = val_high


    # --- Novo parser de operandos de memória: suporta [reg], [imm], [reg+disp], [reg+reg+disp] ---
    def _parse_memory_operand(self, content):
        """
        Recebe o conteúdo dentro de colchetes, ex: 'bx+si+0x10' ou '0x200' ou 'bx-4'
        Retorna o offset (inteiro) resultante.
        """
        # Normaliza: remove espaços e converte '-' em '+-' para facilitar split
        s = content.replace(' ', '').replace('-', '+-')
        parts = [p for p in s.split('+') if p != '']
        offset = 0
        for part in parts:
            if part == '':
                continue
            # sinal negativo?
            try:
                # tenta interpretar como inteiro (0x.. ou decimal)
                val = int(part, 0)
                offset += val
                continue
            except Exception:
                pass
            # se for registrador
            try:
                regval = self.cpu.get_reg(part)
                offset += regval
                continue
            except Exception:
                raise ValueError(f"Parte do operando de memória inválida: '{part}'")
        return offset & 0xFFFF
    
    def _decode_memory_address(self, expr):
        """
         Decodifica um operando de memória no estilo 8086:
         Suporta: [BX], [SI], [DI], [BP],
                 [BX+SI], [BX+DI], [BP+SI], [BP+DI],
                 e variantes com deslocamento: [BX+SI+10h], [BP+20], [BX+10], etc.
         Retorna um inteiro 0..0xFFFF com o endereço físico-offset (ainda sem aplicar segmento).
         Se expr não for um operando de memória (não começar com '[' e terminar com ']'), retorna None.
         """
        if not (isinstance(expr, str) and expr.startswith('[') and expr.endswith(']')):
            return None

        inner = expr[1:-1].strip().lower()
        if inner == '':
            raise ValueError(f"Endereço de memória vazio: {expr}")

        # remove espaços e normaliza sinais '+'
        inner = inner.replace(' ', '')
        parts = inner.split('+')

        base = 0
        regs = []

        for part in parts:
            if part == '':
                continue
            # registradores válidos
            if part in ('bx', 'bp', 'si', 'di'):
                regs.append(part)
                continue

            # hex estilo x86 (10h)
            if part.endswith('h'):
                hexpart = part[:-1]
                if hexpart == '':
                    raise ValueError(f"Deslocamento inválido em {expr}: '{part}'")
                if not all(c in "0123456789abcdef" for c in hexpart):
                    raise ValueError(f"Deslocamento hex inválido em {expr}: '{part}'")
                base += int(hexpart, 16)
                continue

            # imediato decimal/0x/octal/etc
            try:
                base += int(part, 0)
                continue
            except Exception:
                raise ValueError(f"Operando inválido no endereço: {part}")

        # soma registradores conforme regras x86 (simples: soma dos registradores presentes)
        for r in regs:
            base += self.cpu.get_reg(r)

        return base & 0xFFFF


    def _get_operand_value(self, operand, bits_hint=16):
        """
        Obtém valor de registrador/imediato/memória.
        Suporta imediatos no estilo x86 (1234h) e addressing completo via _decode_memory_address.
        """
        if not isinstance(operand, str):
            operand = str(operand)

        op = operand.strip().lower()

        # 1) Memória? Delegar ao decodificador
        addr = self._decode_memory_address(op)
        if addr is not None:
            return self._read_memory(addr, bits_hint)

        # 2) Imediato estilo x86 (7fffh)
        if op.endswith('h') and ('[' not in op) and ('+' not in op):
            hexpart = op[:-1]
            if hexpart != '' and all(c in "0123456789abcdef" for c in hexpart):
                return int(hexpart, 16)

        # 3) Registrador?
        try:
            return self.cpu.get_reg(op)
        except Exception:
            pass

        # 4) Imediato padrão Python (0x..., decimal, etc.)
        try:
            return int(op, 0)
        except Exception:
            raise ValueError(f"Operando '{operand}' inválido")


    def _set_operand_value(self, operand, value, bits_hint=16):
        """
        Define valor em registrador ou destino de memória.
        Suporta addressing mode x86 via _decode_memory_address.
        """
        if not isinstance(operand, str):
            operand = str(operand)

        op = operand.strip().lower()

        # Memória?
        addr = self._decode_memory_address(op)
        if addr is not None:
            # escreve usando segmento padrão (DS) — chamadas de pilha devem especificar 'ss' quando necessário
            self._write_memory(addr, value, bits_hint)
            self.log_print(f"   [MEM] Escreveu {value:04X}h em DS:{addr:04X}h\n")
            return

        # registrador?
        try:
            self.cpu.set_reg(op, value)
            return
        except Exception:
            pass

        raise ValueError(f"Destino '{operand}' inválido")


    def log_print(self, message):
        self.output_log += str(message)

    def load_program_from_text(self, assembly_code_text, initial_segments=None):
        """
        Carrega o programa. Faz uma "pré-compilação" em duas passagens
        para encontrar e registrar todos os rótulos (labels).
        Agora suporta:
         - Diretivas simples: CONST NAME = value
         - Ignora comentários em linhas com ';'
         - Ignora linhas em branco
         - Trata labels com espaços ao redor
        """
        self.cpu.reset()
        self.constants = {}

        if initial_segments:
            # Itera sobre o dicionário: {'cs': 0, 'ds': 10...}
            for reg, val in initial_segments.items():
                try:
                    # Usa o set_reg da CPU (já converte string para int)
                    self.cpu.set_reg(reg, int(val))
                except Exception:
                    pass

        self.cpu.set_reg('ip', 0)
        cs = self.cpu.get_reg('cs')

        raw_lines = assembly_code_text.split('\n')
        lines = []
        # Pré-processamento: remove comentários e espaços; captura diretivas CONST
        for raw in raw_lines:
            line = raw.split(';')[0].strip()
            if not line:
                continue
            # Diretiva CONST: ex "CONST BUF = 0x100"
            m = re.match(r'^(CONST|const)\s+([A-Za-z_]\w*)\s*=\s*(.+)$', line)
            if m:
                name = m.group(2).lower()
                val = int(m.group(3).strip(), 0)
                self.constants[name] = val
                continue
            lines.append(line)

        self.labels = {}
        self.program = {}

        # Passagem 1: Mapear Labels (calculando offsets)
        temp_offset = 0
        for line in lines:
            if line.endswith(':'):
                self.labels[line[:-1].strip().lower()] = temp_offset
            else:
                parts = line.split(maxsplit=1)
                ops = []
                if len(parts) > 1:
                    ops = [x.strip() for x in parts[1].split(',')]
                    # substitui constantes em operandos
                    ops = [str(self.constants.get(o.lower(), o)) for o in ops]
                size = self._get_instruction_size(ops)
                temp_offset += size

        # Passagem 2: Carregar Mapa (IP -> instrução)
        current_offset = 0
        for line in lines:
            if line.endswith(':'): continue
            parts = line.split(maxsplit=1)
            opcode = parts[0].upper()
            operands = []
            if len(parts) > 1:
                operands = [x.strip() for x in parts[1].split(',')]
                operands = [str(self.constants.get(op.lower(), op)) for op in operands]
            size = self._get_instruction_size(operands)
            address = self.get_physical_address('cs', current_offset)
            self.program[address] = (opcode, operands, size)
            current_offset += size

    def run(self):
        """Executa o programa carregado"""
        self.cpu.set_reg('ip', 0)

        max_instructions = 10000
        count = 0
        self.trace_hardware = True

        while count < max_instructions:
            ip = self.cpu.get_reg('ip')
            cs = self.cpu.get_reg('cs')
            address = self.get_physical_address('cs', ip)

            if address not in self.program:
                break

            opcode, operands, size = self.program[address]

            # Avança IP para próxima instrução (comportamento previsto)
            self.cpu.set_reg('ip', ip + size)
            self.cpu.dump()

            try:
                self.log_print(f"[IP={ip:04X}] Executando: {opcode} {', '.join(operands)}\n")
                self.execute_instruction(opcode, operands)
            except Exception as e:
                self.log_print(f"Erro Fatal: {e}")
                break

            count += 1

    def execute_instruction(self, opcode, operands):
        """Decodificador e executor de instruções (COMPLETO com correções)"""

        # --- Grupo de Movimentação ---
        if opcode == 'MOV':
            dest, src = operands[0], operands[1]
            bits = 8 if self._is_reg_8bit(dest) or self._is_reg_8bit(src) else 16
            value = self._get_operand_value(src, bits)
            self._set_operand_value(dest, value, bits)

        elif opcode == 'PUSH':
            src = operands[0]
            value = self._get_operand_value(src, 16) # PUSH é sempre 16-bit
            sp = (self.cpu.get_reg('sp') - 2) & 0xFFFF
            self.cpu.set_reg('sp', sp)
            # PILHA deve usar SS
            self._write_memory(sp, value, 16, segment='ss')

        elif opcode == 'POP':
            dest = operands[0]
            sp = self.cpu.get_reg('sp')
            # PILHA deve usar SS
            value = self._read_memory(sp, 16, segment='ss') # POP é sempre 16-bit
            self.cpu.set_reg('sp', (sp + 2) & 0xFFFF)
            self._set_operand_value(dest, value, 16)

        elif opcode == 'XCHG':
            dest, src = operands[0], operands[1]
            bits = 8 if self._is_reg_8bit(dest) or self._is_reg_8bit(src) else 16
            val_dest = self._get_operand_value(dest, bits)
            val_src = self._get_operand_value(src, bits)
            self._set_operand_value(src, val_dest, bits)
            self._set_operand_value(dest, val_src, bits)

        # --- Grupo Aritmético ---
        elif opcode in ('ADD', 'SUB'):
            dest, src = operands[0], operands[1]
            bits = 8 if self._is_reg_8bit(dest) or self._is_reg_8bit(src) else 16
            val_dest = self._get_operand_value(dest, bits)
            val_src = self._get_operand_value(src, bits)
            if opcode == 'ADD':
                result = val_dest + val_src
                self._set_operand_value(dest, result, bits)
                self.cpu.set_flags_full(val_dest, val_src, result, op='add', bits=bits)
            else:
                result = (val_dest - val_src) & ((1 << (bits+1)) - 1)
                self._set_operand_value(dest, result, bits)
                self.cpu.set_flags_full(val_dest, val_src, result, op='sub', bits=bits)

        elif opcode in ('INC', 'DEC'):
            dest = operands[0]
            bits = 8 if self._is_reg_8bit(dest) else 16
            val_dest = self._get_operand_value(dest, bits)
            result = (val_dest + 1) if opcode == 'INC' else (val_dest - 1)
            self._set_operand_value(dest, result, bits)
            # INC/DEC não alteram CF no x86; mantemos CF e calculamos OF/ZF/SF
            # Chamamos set_flags_full com incdec_cf_unchanged=True para preservar CF
            self.cpu.set_flags_full(val_dest, 1 if opcode=='INC' else 1, result, op='add' if opcode=='INC' else 'sub', bits=bits, incdec_cf_unchanged=True)

        elif opcode == 'NEG':
            dest = operands[0]
            bits = 8 if self._is_reg_8bit(dest) else 16
            val_dest = self._get_operand_value(dest, bits)
            result = (-val_dest) & ((1 << bits) - 1)
            self._set_operand_value(dest, result, bits)
            # NEG sets CF if operand != 0. OF is set when negating the most negative number.
            self.cpu.flags['CF'] = 1 if val_dest != 0 else 0
            # OF for NEG: set if operand == signbit (i.e. cannot be represented)
            signbit = 1 << (bits-1)
            self.cpu.flags['OF'] = 1 if (val_dest & signbit) != 0 and val_dest != 0 else 0
            # ZF and SF
            self.cpu.set_flags_arith(result, bits)

        elif opcode == 'MUL':
            src = operands[0]
            bits = 8 if self._is_reg_8bit(src) else 16
            val_src = self._get_operand_value(src, bits)
            if bits == 8:
                # 8-bit: AX = AL * SRC
                result = (self.cpu.get_reg('al') * val_src) & 0xFFFF
                self.cpu.set_reg('ax', result)
            else:
                # 16-bit: DX:AX = AX * SRC
                result = self.cpu.get_reg('ax') * val_src
                self.cpu.set_reg('ax', result & 0xFFFF)
                self.cpu.set_reg('dx', (result >> 16) & 0xFFFF)

        elif opcode == 'DIV':
            src = operands[0]
            bits = 8 if self._is_reg_8bit(src) else 16
            val_src = self._get_operand_value(src, bits)
            if val_src == 0: raise ZeroDivisionError("Divisão por zero")
            if bits == 8:
                # 8-bit: AL = AX / SRC, AH = AX % SRC
                dividend = self.cpu.get_reg('ax')
                quotient = dividend // val_src; remainder = dividend % val_src
                self.cpu.set_reg('al', quotient)
                self.cpu.set_reg('ah', remainder)
            else:
                # 16-bit: AX = DX:AX / SRC, DX = DX:AX % SRC
                dividend = (self.cpu.get_reg('dx') << 16) | self.cpu.get_reg('ax')
                quotient = dividend // val_src; remainder = dividend % val_src
                self.cpu.set_reg('ax', quotient)
                self.cpu.set_reg('dx', remainder)

        # --- Grupo Booleano ---
        elif opcode in ('AND', 'OR', 'XOR'):
            dest, src = operands[0], operands[1]
            bits = 8 if self._is_reg_8bit(dest) or self._is_reg_8bit(src) else 16
            val_dest = self._get_operand_value(dest, bits)
            val_src = self._get_operand_value(src, bits)
            if   opcode == 'AND': result = val_dest & val_src
            elif opcode == 'OR':  result = val_dest | val_src
            elif opcode == 'XOR': result = val_dest ^ val_src
            self._set_operand_value(dest, result, bits)
            self.cpu.set_flags_arith(result, bits)

        elif opcode == 'NOT':
            dest = operands[0]
            bits = 8 if self._is_reg_8bit(dest) else 16
            val_dest = self._get_operand_value(dest, bits)
            mask = 0xFFFF if bits == 16 else 0xFF
            result = (~val_dest) & mask # Inverte e aplica máscara
            self._set_operand_value(dest, result, bits)
            # NOT não afeta as flags

        # --- Grupo de Teste/Pulo ---
        elif opcode == 'CMP':
            src1, src2 = operands[0], operands[1]
            bits = 8 if self._is_reg_8bit(src1) or self._is_reg_8bit(src2) else 16
            val1 = self._get_operand_value(src1, bits)
            val2 = self._get_operand_value(src2, bits)
            result = (val1 - val2) & ((1 << (bits+1)) - 1)
            self.log_print(f"CMP ({bits}-bit): {val1} - {val2} = {result}")
            # CMP behaves like SUB for flags
            self.cpu.set_flags_full(val1, val2, result, op='sub', bits=bits)

        elif opcode == 'JMP':
            dest_label = operands[0].lower()
            if dest_label not in self.labels:
                raise ValueError(f"Rótulo de pulo '{dest_label}' não encontrado")
            self.cpu.set_reg('ip', self.labels[dest_label])
            self.log_print(f"JMP para {dest_label} (IP={self.labels[dest_label]})")

        # Jumps Condicionais
        elif opcode in ('JE', 'JNE', 'JG', 'JGE', 'JL', 'JLE'):
            ZF = self.cpu.flags['ZF']
            SF = self.cpu.flags['SF']
            OF = self.cpu.flags['OF']

            condition_met = False
            # Lógica de pulo "signed" com OF considerado
            if   opcode == 'JE':  condition_met = (ZF == 1)
            elif opcode == 'JNE': condition_met = (ZF == 0)
            elif opcode == 'JG':  condition_met = (ZF == 0 and SF == OF)
            elif opcode == 'JGE': condition_met = (SF == OF)
            elif opcode == 'JL':  condition_met = (SF != OF)
            elif opcode == 'JLE': condition_met = (ZF == 1 or SF != OF)

            if condition_met:
                dest_label = operands[0].lower()
                target_ip = self.labels[dest_label]
                self.cpu.set_reg('ip', target_ip)
                self.log_print(f"{opcode}: Condição satisfeita. Pulando para {dest_label} (IP={target_ip})")
            else:
                self.log_print(f"{opcode}: Condição não satisfeita. Não pulando.")

        # --- Procedimentos e Loops ---
        elif opcode == 'CALL':
            dest_label = operands[0].lower()
            ip = self.cpu.get_reg('ip')
            sp = (self.cpu.get_reg('sp') - 2) & 0xFFFF
            self.cpu.set_reg('sp', sp)
            # PUSH IP na pilha (SS)
            self._write_memory(sp, ip, 16, segment='ss')
            self.log_print(f"CALL: Salvando IP={ip} na pilha [{sp}]")
            # JMP para o label
            target_ip = self.labels[dest_label]
            self.cpu.set_reg('ip', target_ip)
            self.log_print(f"CALL: Pulando para {dest_label} (IP={target_ip})")

        elif opcode == 'RET':
            sp = self.cpu.get_reg('sp')
            ip = self._read_memory(sp, 16, segment='ss')
            self.cpu.set_reg('sp', (sp + 2) & 0xFFFF)
            self.cpu.set_reg('ip', ip)
            self.log_print(f"RET: Restaurando IP={ip} da pilha. Novo SP={self.cpu.get_reg('sp')}")

        elif opcode == 'IRET':
            sp = self.cpu.get_reg('sp')
            ip = self._read_memory(sp, 16, segment='ss')
            self.cpu.set_reg('sp', (sp + 2) & 0xFFFF)
            self.cpu.set_reg('ip', ip)
            self.log_print("Aviso: IRET simulado como RET.")

        elif opcode == 'LOOP':
            dest_label = operands[0].lower()
            cx = (self.cpu.get_reg('cx') - 1) & 0xFFFF
            self.cpu.set_reg('cx', cx)
            if cx != 0:
                target_ip = self.labels[dest_label]
                self.cpu.set_reg('ip', target_ip)
                self.log_print(f"LOOP: CX={cx}, pulando para {dest_label} (IP={target_ip})")
            else:
                self.log_print(f"LOOP: CX={cx}, não pulando.")

        # --- I/O ---
        elif opcode == 'IN':
            dest, port = operands[0], operands[1]
            # Simulação: retorna 0 para evitar bloqueio
            val = 0
            self.log_print(f"[IN] Lendo porta {port} -> {val}\n")
            self._set_operand_value(dest, val)

        elif opcode == 'OUT':
            port, src = operands[0], operands[1]
            val = self._get_operand_value(src)
            self.log_print(f"Simulador (OUT): Porta {port} recebeu valor {val}")

        else:
            raise NotImplementedError(f"Instrução '{opcode}' desconhecida ou não implementada.")

    def step(self):
        self.trace_hardware = True
        ip = self.cpu.get_reg('ip')
        cs = self.cpu.get_reg('cs')

        address = self.get_physical_address('cs', ip)

        if address not in self.program:
            return "END"

        opcode, operands, size = self.program[address]

        self.cpu.set_reg('ip', (ip + size) & 0xFFFF)

        try:
            self.log_print(f"[ADDR: {address:05X} | CS:IP {cs:04X}:{ip:04X}] Executando: {opcode} {', '.join(operands)}")
            self.execute_instruction(opcode, operands)
        except Exception as e:
            return f"Erro ao executar: {e}"

        return "OK"

    def reset(self):

        self.cpu.reset()
        self.cpu.set_reg("ip", 0)

        self.halted = False
        self.labels = {}
        self.program = {}
        self.output_log = ""

        return "RESET_OK"

    def get_state_json(self):

        dump = self.cpu.dump()

        ds_val = self.cpu.get_reg('ds')
        start_phys = (ds_val << 4) & 0xFFFFFFFF

        # Pega uma fatia de 256 bytes a partir do início do DS
        end_phys = min(start_phys + 256, len(self.memory))
        mem_view = list(self.memory[start_phys : end_phys])

        # Se a fatia for menor que 256 (fim da RAM), preenche com zeros para não quebrar UI
        if len(mem_view) < 256:
            mem_view += [0] * (256 - len(mem_view))

        return {
            "state": {
                "registers": dump['registers'],
                "flags": dump['flags'],
                "memory": mem_view
            },
            "logs": self.output_log.split('\n') if self.output_log else []
        }
