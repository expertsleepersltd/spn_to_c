'''
    Copyright (C) 2024 Expert Sleepers Ltd

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

import sys
import re

filename = sys.argv[1]

defines = []
declarations = []
mem = {}
code = []
number = 1
usedLabels = []
usedLFOs = []

register_names = [ 'pot0', 'pot1', 'pot2', 'adcl', 'adcr', 'dacl', 'dacr', 'addr_ptr', 'rmp0_rate', 'rmp1_rate', 'sin0_rate', 'sin1_rate', 'sin0_range', 'sin1_range', 'sin0', 'sin1', 'rmp0', 'rmp1' ]

for r in register_names:
	defines.append( f'#define {r} (state->{r})' )
	u = r.upper()
	defines.append( f'#define {u} {r}' )

for r in range(32):
	defines.append( f'#define reg{r} (state->reg{r})' )
	defines.append( f'#define REG{r} reg{r}' )

def choFlags( x ):
	bits = []
	for b in x.split('|'):
		if b.startswith( '0x' ) or b.isnumeric():
			bits.append( b )
		elif len(b) == 0:
			bits.append( '0' )
		else:
			bits.append( 'cho_' + b.lower() )
	return '|'.join( bits )

def convertArg( x ):
	if x.startswith( '%' ):
		return '0b' + x[1:].replace( '_', '' )
	if x.startswith( '$' ):
		return '0x' + x[1:]
	return x.replace( '/', '/(float)' )

def checkRegisterName( x ):
	if x.isnumeric():
		return 'state->registers[' + x + ']'
	return x

def parseAddress( mm ):
	try:
		bits = re.split( '([\\+-])', mm, 1 )
		m = bits[0]
		if m.endswith( '#' ):
			m = m[:-1]
			sz = mem[m][0]
			m += '+' + str( sz ) + '-1'
		elif m.endswith( '^' ):
			m = m[:-1]
			sz = mem[m][0]
			m += '+((' + str( sz ) + ')/2)'
		return m + ''.join( bits[1:] )
	except:
		raise Exception( 'unable to parse address ' + mm + ':' + str( mem ) )

anyDel = False
anyPacc = False

with open( filename, 'r' ) as F:
	lines = F.readlines()
	lines = [ l.strip() for l in lines ]
	for x in lines:
		bits = [ b.strip() for b in x.split( ';' ) ]
		toks = bits[0].split()
		comments = ''
		if len( bits ) > 1:
			comments = '\t\t// ' + bits[1]
		if len( toks ) == 3 and toks[1].lower() == 'equ':
			toks[1] = toks[0]
			toks[0] = 'equ'
		if len( toks ) == 3 and toks[1].lower() == 'mem':
			toks[1] = toks[0]
			toks[0] = 'mem'
		if len( toks ):
			opcode = toks[0].lower()
			if opcode == 'equ':
				line = '#define ' + toks[1] + ' (' + toks[2] + ')'
				defines.append( line + comments )
			elif opcode == 'mem':
				mem[ toks[1] ] = [ toks[2], comments ]
			else:
				pacc = False
				if opcode == 'skp':
					args = ''.join(toks[1:]).split( ',' )
					line = '';
					if args[0].lower() == 'zro':
						line = 'if ( e.acc == 0 ) '
					elif args[0].lower() == 'gez':
						line = 'if ( e.acc >= 0 ) '
					elif args[0].lower() == 'neg':
						line = 'if ( e.acc < 0 ) '
					elif args[0].lower() == 'run':
						line = 'if ( state->run ) '
					else:
						raise Exception( 'cannot parse skp condition: ' + args[0] )
					label = args[1]
					if label.isdecimal():
						label = number + 1 + int(label)
					else:
						pass
					usedLabels.append( label )
					line += 'goto l' + str( label ) + ';'
				elif opcode in [ 'rdax', 'wrax', 'mulx', 'rdfx', 'log', 'exp', 'sof', 'ldax', 'absa', 'and', 'or', 'xor', 'rmpa', 'maxx' ]:
					args = ''.join(toks[1:]).split( ',' )
					args = [ convertArg( a ) for a in args ]
					if opcode.endswith( 'x' ):
						args[0] = checkRegisterName( args[0] )
					if opcode in [ 'and', 'or', 'xor' ]:
						opcode = 'bitwise_' + opcode
					line = 'e.' + opcode + '( ' + ','.join( args ) + ' );'
				elif opcode in [ 'wrhx', 'wrlx' ]:
					args = ''.join(toks[1:]).split( ',' )
					args = [ convertArg( a ) for a in args ]
					args[0] = checkRegisterName( args[0] )
					line = 'e.' + opcode + '( ' + ','.join( args ) + ',pacc );'
					pacc = True
					anyPacc = True
				elif opcode == 'wldr':
					args = ''.join(toks[1:]).split( ',' )
					if args[0].lower().startswith( 'rmp' ):
						args[0] = args[0][3:]
					line = 'e.' + opcode + '( ' + ','.join( args ) + ' );'
				elif opcode == 'wlds':
					args = ''.join(toks[1:]).split( ',' )
					if args[0].lower().startswith( 'sin' ):
						args[0] = args[0][3:]
					line = 'e.' + opcode + '( ' + ','.join( args ) + ' );'
				elif opcode in [ 'rda', 'wra', 'wrap' ]:
					args = ''.join(toks[1:]).split( ',' )
					m = parseAddress( args[0] )
					addr = 'state->delay_ptr[ ( downcounter + ' + m + ' + 32768 ) & 32767 ]'
					line = 'e.' + opcode + '( ' + addr + ',' + args[1] + ' );'
					anyDel = True
				elif opcode == 'cho':
					args = ''.join(toks[1:]).split( ',' )
					lfo = args[1].lower()
					if args[0].lower() == 'rda':
						if len(args) < 4:
							args.append( args[2] )
							args[2] = ''
						flags = choFlags( args[2] )
						m = parseAddress( args[3] )
						line = 'e.cho_rda( cho_' + lfo + ',' + flags + ', downcounter + ' + m + ' );'
						anyDel = True
					elif args[0].lower() == 'rdal':
						line = 'e.cho_rdal( ' + checkRegisterName( lfo ) + ' );'
					elif args[0].lower() == 'sof':
						flags = choFlags( args[2] )
						line = 'e.cho_sof( cho_' + lfo + ',' + flags + ', ' + args[3] + ' );'
					else:
						raise Exception( 'unknown cho: ' + args[0] )
					usedLFOs.append( lfo )
				elif opcode in [ 'clr' ]:
					line = 'e.' + opcode + '();'
				elif opcode in [ 'jam' ]:
					line = 'e.' + opcode + '( jam_' + toks[1] + ' );'
				elif opcode.endswith( ':' ):
					line = 'l' + toks[0]
				else:
					raise Exception( 'unknown opcode: ' + opcode )
				code.append( [ number, line, comments, pacc ] )
				number += 1
		else:
				code.append( [ -1, '', comments, False ] )

print( '#include <spinner.h>' )
print( 'using namespace _three_pot;' )

for x in defines:
	print( x )

for x in declarations:
	print( x )

offset = '0'
for x, y in mem.items():
	print( '#define', x, '(', offset, ')', y[1] )
	offset += '+' + y[0]

print( 'void process( _three_pot::_state* state ) {' )

print( '    _spinner e( state );' )
if anyDel:
	print( '    uint32_t downcounter = state->downcounter;' )
if anyPacc:
	print( '    float pacc;' )

for i in range( len( code ) ):
	x = code[i]
	if x[0] in usedLabels:
		print( 'l' + str( x[0] ) + ':' )
	elif x[1].endswith( ':' ):
		if x[1][1:-1] not in usedLabels:
			continue
	if i < len( code ) - 1:
		if code[i+1][3]:
			print( '    pacc = e.acc;' )
	print( '    ' + x[1] + x[2] )

for lfo in [ 'rmp0', 'rmp1', 'sin0', 'sin1' ]:
	if lfo in usedLFOs:
		print( f'    e.update_{lfo}();' )

print( '}' )
