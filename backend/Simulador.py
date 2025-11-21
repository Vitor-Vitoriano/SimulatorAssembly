 
 # -*- coding: utf-8 -*-
import sys

class CPU:
    """
    Simula os registradores da CPU x86 16-bit (Modo Real).
    Implementa o acesso aos registradores de 8-bit (high/low).
    """
    def __init__(self):
        # Dicionário interno para os registradores de 16-bit
        self._registers = {
            'ax': 0, 'bx': 0, 'cx': 0, 'dx': 0,
            'si': 0, 'di': 0, 'bp': 0, 'sp': 0, 'ip': 0,
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

    def set_flags_arith(self, result, bits=16):
        """Helper para definir flags ZF e SF"""
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
        
        # (Opcional: print para debug)
        # print(f"Flags atualizados ({bits}-bit): ZF={self.flags['ZF']}, SF={self.flags['SF']}")

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
    
    def dump_print(self):
        """Exibe o estado atual dos registradores 16-bit"""
        print("--- CPU (16-bit) ---")
        regs1 = f"AX: {self.get_reg('ax'):<5} BX: {self.get_reg('bx'):<5} CX: {self.get_reg('cx'):<5} DX: {self.get_reg('dx'):<5}"
        regs2 = f"SI: {self.get_reg('si'):<5} DI: {self.get_reg('di'):<5} BP: {self.get_reg('bp'):<5} SP: {self.get_reg('sp'):<5}"
        regs3 = f"IP: {self.get_reg('ip'):<5} FLAGS [ZF:{self.flags['ZF']} SF:{self.flags['SF']} OF:{self.flags['OF']} CF:{self.flags['CF']}]"
        print(regs1); print(regs2); print(regs3)
        print("----------------------")

    def reset(self):
        for r in self._registers:
            self._registers[r] = 0
        self._flags = {
            "zf": 0,
            "cf": 0,
            "sf": 0,
            "of": 0
        }

class Simulator:
    """O Simulador principal com todas as instruções do A3."""
    
    def __init__(self, memory_size=65536): # 64k de BYTES
        self.cpu = CPU()
        self.memory = bytearray(memory_size) # Memória byte-addressable
        self.program = {}
        self.labels = {}  # Dicionário para guardar rótulos (Labels)
        self.output_log = ""

        # Pilha começa no topo da memória
        self.cpu.set_reg('sp', 0xFFFE)
        self.cpu.set_reg('bp', 0xFFFE)

    def _is_reg_8bit(self, reg_name):
        """Checa se um nome de registrador é 8-bit"""
        return reg_name.lower() in ('al', 'ah', 'bl', 'bh', 'cl', 'ch', 'dl', 'dh')

    def _get_instruction_size(self, operands):
     
        size = 2  # (Opcode)
        size += len(operands) * 2 # Cada operando adiciona 2 bytes
        return size

    def get_physical_address(self, segment_reg, offset):
        """
        Calcula Endereço Físico = (Segmento * 16) + Offset
        """
        seg_val = self.cpu.get_reg(segment_reg)
        
        # Garante 16-bit unsigned para o offset
        offset = offset & 0xFFFF 
        
        physical_addr = (seg_val << 4) + offset
        
        if physical_addr >= len(self.memory):
            # Em simulação simples, podemos fazer wrap-around ou dar erro
            # Vamos fazer wrap-around (comportamento padrão x86)
            physical_addr %= len(self.memory)
            
        return physical_addr
    
    def _read_memory(self, offset, bits=16, segment='ds'):
        """Lê 8 ou 16 bits da memória (Little-Endian)"""
        address = self.get_physical_address(segment, offset)
            
        if bits == 8:
            return self.memory[address]
        
        # Little-Endian: Baixo byte no endereço menor
        val_low = self.memory[address]
        val_high = self.memory[address + 1]
        return (val_high << 8) | val_low

    def _write_memory(self, offset, value, bits=16, segment='ds'):
        """Escreve 8 ou 16 bits na memória (Little-Endian)"""
        address = self.get_physical_address(segment, offset)

        if bits == 8:
            self.memory[address] = value & 0xFF
            return
        
        # Little-Endian: Baixo byte no endereço menor
        val_low = value & 0xFF
        val_high = (value >> 8) & 0xFF
        self.memory[address] = val_low
        self.memory[address + 1] = val_high

    def _get_operand_value(self, operand, bits_hint=16):
        """
        Pega o VALOR de um operando (registrador, imediato, ou memória).
        """
        operand = operand.lower()
        
        # Ponteiro de memória (Ex: [0x100], [bx])
        if operand.startswith('[') and operand.endswith(']'):
            address_str = operand[1:-1]
            try: address = int(address_str, 0)
            except ValueError: address = self.cpu.get_reg(address_str)
            return self._read_memory(address, bits_hint)
            
        # Registrador
        try: return self.cpu.get_reg(operand)
        except ValueError: pass
            
        # Valor imediato
        try: return int(operand, 0)
        except ValueError: raise ValueError(f"Operando '{operand}' inválido")

    def _set_operand_value(self, operand, value, bits_hint=16):
        """
        Define o VALOR de um operando (DESTINO).
        """
        operand = operand.lower()
        
        # Ponteiro de memória
        if operand.startswith('[') and operand.endswith(']'):
            address_str = operand[1:-1]
            try: address = int(address_str, 0)
            except ValueError: address = self.cpu.get_reg(address_str)
            self._write_memory(address, value, bits_hint)
            # (Opcional: print para debug)
            # print(f"Memória[{address}] definida como {value} ({bits_hint}-bit)")
            
        # Registrador
        else:
            try: self.cpu.set_reg(operand, value)
            except ValueError: raise ValueError(f"Destino '{operand}' inválido")

    def log_print(self, message):
        self.output_log += str(message)

    def load_program_from_text(self, assembly_code_text, initial_segments=None):
        """
        Carrega o programa. Faz uma "pré-compilação" em duas passagens
        para encontrar e registrar todos os rótulos (labels).
        """
        self.program = {}
        self.labels = {}
        self.output_log = ""
        self.cpu.set_reg('ip', 0)
        self.cpu.set_reg('cs', 0)

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

        lines = assembly_code_text.strip().split('\n')
        current_offset = 0

        # Passagem 1: Mapear Labels
        temp_offset = 0
        for line in lines:
            line = line.strip().split(';')[0].strip()
            if not line: continue
            
            if line.endswith(':'):
                self.labels[line[:-1].lower()] = temp_offset
            else:
                # Calcula tamanho para saber onde fica o próximo label
                parts = line.split(maxsplit=1)
                ops = [x.strip() for x in parts[1].split(',')] if len(parts) > 1 else []
                size = self._get_instruction_size(ops)
                temp_offset += size

        # Passagem 2: Carregar Mapa
        for line in lines:
            line = line.strip().split(';')[0].strip()
            if not line or line.endswith(':'): continue

            parts = line.split(maxsplit=1)
            opcode = parts[0].upper()
            operands = [x.strip() for x in parts[1].split(',')] if len(parts) > 1 else []
            
            size = self._get_instruction_size(operands)
            
            # Armazena no mapa lógico (IP -> Instrução)
            address = self.get_physical_address('cs', current_offset)
            self.program[address] = (opcode, operands, size)
            current_offset += size

    def run(self):
        """Executa o programa carregado"""
        self.cpu.set_reg('ip', 0)

        max_instructions = 1000
        count = 0
        
        while count < max_instructions:
            ip = self.cpu.get_reg('ip')
            cs = self.cpu.get_reg('cs')
            address = self.get_physical_address('cs', ip)

            if address not in self.program:
                break
            
            opcode, operands, size = self.program[address]
                
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
        """Decodificador e executor de instruções (COMPLETO)"""
        
        # --- Grupo de Movimentação ---
        if opcode == 'MOV':
            dest, src = operands[0], operands[1]
            bits = 8 if self._is_reg_8bit(dest) or self._is_reg_8bit(src) else 16
            value = self._get_operand_value(src, bits)
            self._set_operand_value(dest, value, bits)

        elif opcode == 'PUSH':
            src = operands[0]
            value = self._get_operand_value(src, 16) # PUSH é sempre 16-bit
            sp = self.cpu.get_reg('sp') - 2
            self.cpu.set_reg('sp', sp)
            self._write_memory(sp, value, 16)

        elif opcode == 'POP':
            dest = operands[0]
            sp = self.cpu.get_reg('sp')
            value = self._read_memory(sp, 16) # POP é sempre 16-bit
            self.cpu.set_reg('sp', sp + 2)
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
            result = (val_dest + val_src) if opcode == 'ADD' else (val_dest - val_src)
            self._set_operand_value(dest, result, bits)
            self.cpu.set_flags_arith(result, bits)

        elif opcode in ('INC', 'DEC'):
            dest = operands[0]
            bits = 8 if self._is_reg_8bit(dest) else 16
            val_dest = self._get_operand_value(dest, bits)
            result = (val_dest + 1) if opcode == 'INC' else (val_dest - 1)
            self._set_operand_value(dest, result, bits)
            self.cpu.set_flags_arith(result, bits)

        elif opcode == 'NEG':
            dest = operands[0]
            bits = 8 if self._is_reg_8bit(dest) else 16
            val_dest = self._get_operand_value(dest, bits)
            result = 0 - val_dest
            self._set_operand_value(dest, result, bits)
            self.cpu.set_flags_arith(result, bits)

        elif opcode == 'MUL':
            src = operands[0]
            bits = 8 if self._is_reg_8bit(src) else 16
            val_src = self._get_operand_value(src, bits)
            if bits == 8:
                # 8-bit: AX = AL * SRC
                result = self.cpu.get_reg('al') * val_src
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
            result = val1 - val2
            print(f"CMP ({bits}-bit): {val1} - {val2} = {result}")
            self.cpu.set_flags_arith(result, bits)

        elif opcode == 'JMP':
            dest_label = operands[0].lower()
            if dest_label not in self.labels:
                raise ValueError(f"Rótulo de pulo '{dest_label}' não encontrado")
            self.cpu.set_reg('ip', self.labels[dest_label])
            print(f"JMP para {dest_label} (IP={self.labels[dest_label]})")

        # Jumps Condicionais
        elif opcode in ('JE', 'JNE', 'JG', 'JGE', 'JL', 'JLE'):
            ZF = self.cpu.flags['ZF']
            SF = self.cpu.flags['SF']
            OF = self.cpu.flags['OF'] # (Não implementado, mas aqui estaria)
            
            condition_met = False
            # Lógica de pulo "signed"
            if   opcode == 'JE':  condition_met = (ZF == 1)
            elif opcode == 'JNE': condition_met = (ZF == 0)
            elif opcode == 'JG':  condition_met = (ZF == 0 and SF == 0) # (SF == OF)
            elif opcode == 'JGE': condition_met = (SF == 0)             # (SF == OF)
            elif opcode == 'JL':  condition_met = (SF == 1)             # (SF != OF)
            elif opcode == 'JLE': condition_met = (ZF == 1 or SF == 1)  # (ZF=1 or SF!=OF)
            
            if condition_met:
                dest_label = operands[0].lower()
                target_ip = self.labels[dest_label]
                self.cpu.set_reg('ip', target_ip)
                print(f"{opcode}: Condição satisfeita. Pulando para {dest_label} (IP={target_ip})")
            else:
                print(f"{opcode}: Condição não satisfeita. Não pulando.")
        
        # --- Procedimentos e Loops ---
        elif opcode == 'CALL':
            dest_label = operands[0].lower()
            # 1. PUSH IP (endereço da *próxima* instrução, que já está no IP)
            ip = self.cpu.get_reg('ip')
            sp = self.cpu.get_reg('sp') - 2
            self.cpu.set_reg('sp', sp)
            self._write_memory(sp, ip, 16)
            print(f"CALL: Salvando IP={ip} na pilha [{sp}]")
            # 2. JMP para o label
            target_ip = self.labels[dest_label]
            self.cpu.set_reg('ip', target_ip)
            print(f"CALL: Pulando para {dest_label} (IP={target_ip})")

        elif opcode == 'RET':
            # 1. POP IP
            sp = self.cpu.get_reg('sp')
            ip = self._read_memory(sp, 16)
            self.cpu.set_reg('sp', sp + 2)
            # 2. JMP para o IP (restaurado)
            self.cpu.set_reg('ip', ip)
            print(f"RET: Restaurando IP={ip} da pilha. Novo SP={self.cpu.get_reg('sp')}")

        elif opcode == 'IRET':
            # Simplificação: IRET faz o mesmo que RET
            sp = self.cpu.get_reg('sp')
            ip = self._read_memory(sp, 16)
            self.cpu.set_reg('sp', sp + 2)
            self.cpu.set_reg('ip', ip)
            print("Aviso: IRET simulado como RET.")

        elif opcode == 'LOOP':
            dest_label = operands[0].lower()
            # 1. Decrementa CX
            cx = self.cpu.get_reg('cx') - 1
            self.cpu.set_reg('cx', cx)
            # 2. Se CX != 0, JMP
            if cx != 0:
                target_ip = self.labels[dest_label]
                self.cpu.set_reg('ip', target_ip)
                print(f"LOOP: CX={cx}, pulando para {dest_label} (IP={target_ip})")
            else:
                print(f"LOOP: CX={cx}, não pulando.")
        
        # --- I/O ---
        elif opcode == 'IN':
            dest, port = operands[0], operands[1]
            # Simulação: Pede input do usuário
            val = 0 # Valor simulado para não travar
            self.log_print(f"[IN] Lendo porta {port} -> {val}\n")
            self._set_operand_value(dest, val)

        elif opcode == 'OUT':
            port, src = operands[0], operands[1]
            val = self._get_operand_value(src)
            # Simulação: Printa no console
            print(f"Simulador (OUT): Porta {port} recebeu valor {val}")

        else:
            raise NotImplementedError(f"Instrução '{opcode}' desconhecida ou não implementada.")


    def step(self):
        ip = self.cpu.get_reg('ip')
        cs = self.cpu.get_reg('cs')

        address = self.get_physical_address('cs', ip)

        if address not in self.program:
            return "END"

        opcode, operands, size = self.program[address]

        self.cpu.set_reg('ip', ip + size)

        opcode, operands, size = self.program[address]
        self.cpu.set_reg('ip', ip + size)
        
        try:
            self.log_print(f"[Endereço IP={ip:04X}] Executando: {opcode} {', '.join(operands)}")
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

        return "RESET_OK"

