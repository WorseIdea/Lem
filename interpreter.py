import struct
import io
import os
import pathlib as path
import sys
from enum import Enum

class instr(Enum):
	nop = 0x00
	push_int = 0x01
	push_str = 0x02
	push_float = 0x03
	push_nil = 0x04
	pop = 0x20
	add = 0x21
	sub = 0x22
	mul = 0x23
	div = 0x24
	store = 0x25
	load = 0x26
	jump = 0x27
	print = 0xA0
	halt = 0xFF

class Interpreter:
	def __init__(self, data):
		self.call_stack = [{"__frame__": 0, "__return__": 0}]
		self.value_stack = []
		self.stream = io.BytesIO(data)
		self.symbols = {}
		
		self.runInitial()
	
	def readUInt8(self):
		d = self.stream.read(1)
		
		if (d == None): return None
		
		[x] = struct.unpack("B", d)
		
		return x
	
	def readUInt16(self):
		d = self.stream.read(2)
		
		if (d == None): return None
		
		[x] = struct.unpack("H", d)
		
		return x
	
	def readUInt32(self):
		d = self.stream.read(4)
		
		if (d == None): return None
		
		[x] = struct.unpack("I", d)
		
		return x
	
	def readUInt64(self):
		d = self.stream.read(8)
		
		if (d == None): return None
		
		[x] = struct.unpack("Q", d)
		
		return x
	
	def readString(self):
		s = bytearray()
		
		while (True):
			c = self.stream.read(1)
			
			if (c == b"\x00"):
				break
			
			s += c
		
		return s.decode("utf-8")
	
	def jump(self, pos):
		self.stream.seek(self.base_pos + pos, os.SEEK_SET)
	
	def tell(self):
		return self.stream.tell()
	
	def push(self, val):
		self.value_stack.append(val)
	
	def pop(self):
		val = self.value_stack[-1]
		self.value_stack = self.value_stack[:-1]
		return val
	
	def runInitial(self):
		# Read initial instruction pointer
		initial_ip = self.readUInt32()
		
		# Read symbols
		sym_count = self.readUInt32()
		
		for i in range(sym_count):
			k = self.readString()
			v = self.readUInt32()
			
			# Note: we need to patch this later
			self.symbols[k] = v
		
		# Read base code pos
		self.base_pos = self.tell()
		
		# Jump to end
		self.jump(initial_ip)
	
	def run(self, ip = None):
		"""
		Run the script from the given position
		"""
		
		if (ip != None):
			self.jump(ip)
		
		while (True):
			opcode = self.readUInt8()
			
			print(hex(self.tell())[2:], "|", hex(opcode)[2:])
			
			match (opcode):
				case 0: # nop
					pass
				
				case 0x01: # push <int>
					self.push(self.readUInt32())
				
				case 0x02: # push <str>
					self.push(self.readString())
				
				case 0x03: # push <float>
					self.push(self.readFloat32()) # !!!
				
				case 0x04: # push <nil>
					self.push(None)
				
				case 0x20: # pop
					self.pop()
				
				case 0x21: # add
					b = self.pop()
					a = self.pop()
					self.push(a + b)
				
				case 0x22: # sub
					b = self.pop()
					a = self.pop()
					self.push(a - b)
				
				case 0x23: # mul
					b = self.pop()
					a = self.pop()
					self.push(a * b)
				
				case 0x24: # div
					b = self.pop()
					a = self.pop()
					self.push(a / b)
				
				case 0x25: # str
					self.call_stack[-1][self.pop()] = self.pop()
				
				case 0x26: # ldr
					self.push(self.call_stack[-1][self.pop()])
				
				case 0x27: # jmp
					self.jump(self.pop())
				
				case 0xA0: # print
					print(self.pop())
				
				case 0xFF: # halt
					break
				
				case _:
					raise BaseException(f"Bad opcode at {self.ip}")
	
	def call(self, symbol = "main"):
		ip = self.symbols.get(symbol, None)
		
		if (ip == None):
			return
		
		print(f"\t{symbol} {hex(ip)[2:]}")
		
		self.run(ip)

def main():
	i = Interpreter(path.Path(sys.argv[1]).read_bytes())
	i.call(sys.argv[2] if len(sys.argv) > 2 else "main")

if (__name__ == "__main__"):
	main()
