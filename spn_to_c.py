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

filename = sys.argv[1]

defines = []
declarations = []
mem = {}
code = []
number = 1
usedLabels = []
usedLFOs = []

defines.append( '#define rmp0_rate (state->rmp0_rate)' )
defines.append( '#define rmp1_rate (state->rmp1_rate)' )
defines.append( '#define sin0_rate (state->sin0_rate)' )
defines.append( '#define sin1_rate (state->sin1_rate)' )
defines.append( '#define sin0_range (state->sin0_range)' )
defines.append( '#define sin1_range (state->sin1_range)' )
defines.append( '#define pot0 state->pot0' )
defines.append( '#define pot1 state->pot1' )
defines.append( '#define pot2 state->pot2' )
defines.append( '#define adcl state->adcl' )
defines.append( '#define adcr state->adcr' )
defines.append( '#define dacl state->dacl' )
defines.append( '#define dacr state->dacr' )
defines.append( '#define addr_ptr state->addr_ptr' )
defines.append( '#define ADCL adcl' )
defines.append( '#define ADCR adcr' )
defines.append( '#define POT0 pot0' )
defines.append( '#define POT1 pot1' )
defines.append( '#define POT2 pot2' )

def choFlags( x ):
	bits = []
	for b in x.split('|'):
		if b.startswith( '0x' ) or b.isnumeric():
			bits.append( b )
		else:
			bits.append( 'cho_' + b )
	return '|'.join( bits )

def convertArg( x ):
	if x.startswith( '%' ):
		return '0b' + x[1:].replace( '_', '' )
	if x.startswith( '$' ):
		return '0x' + x[1:]
	if x.startswith( 'reg' ):
		return 'state->' + x
	return x.replace( '/', '/(float)' )

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
		if len( toks ):
			opcode = toks[0]
			if opcode == 'equ':
				if toks[2].startswith( 'reg' ):
					line = '#define ' + toks[1] + ' (state->' + toks[2] + ')'
					declarations.append( line + comments )
				else:
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
				elif opcode in [ 'rdax', 'wrax', 'mulx', 'rdfx', 'log', 'exp', 'sof', 'ldax', 'absa', 'and', 'or', 'rmpa', 'maxx' ]:
					args = ''.join(toks[1:]).split( ',' )
					args = [ convertArg( a ) for a in args ]
					if opcode in [ 'and', 'or' ]:
						opcode = 'bitwise_' + opcode
					line = 'e.' + opcode + '( ' + ','.join( args ) + ' );'
				elif opcode in [ 'wrhx', 'wrlx' ]:
					args = ''.join(toks[1:]).split( ',' )
					args = [ convertArg( a ) for a in args ]
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
					m = args[0]
					mod = 0
					if '-' in m:
						bits = m.split( '-', 1 )
						m = bits[0]
						mod = -int( bits[1] )
					elif '+' in m:
						bits = m.split( '+', 1 )
						m = bits[0]
						mod = int( bits[1] )
					if m.endswith( '#' ):
						m = m[:-1]
						sz = int( mem[m][0] )
						offset = sz - 1
					elif m.endswith( '^' ):
						m = m[:-1]
						sz = int( mem[m][0] )
						offset = sz / 2
					else:
						offset = 0
					offset += mod
					addr = 'state->delay_ptr[ ( del + ' + m + ' + ' + str( offset ) + ' + 32768 ) & 32767 ]'
					line = 'e.' + opcode + '( ' + addr + ',' + args[1] + ' );'
					anyDel = True
				elif opcode == 'cho':
					args = ''.join(toks[1:]).split( ',' )
					lfo = args[1].lower()
					if args[0].lower() == 'rda':
						flags = choFlags( args[2] )
						line = 'e.cho_rda( cho_' + lfo + ',' + flags + ', del+' + args[3] + ' );'
						anyDel = True
					elif args[0].lower() == 'rdal':
						line = 'e.cho_rdal( state->' + lfo + ' );'
					elif args[0].lower() == 'sof':
						flags = choFlags( args[2] )
						line = 'e.cho_sof( cho_' + lfo + ',' + flags + ', ' + args[3] + ' );'
					else:
						raise Exception( 'unknown cho: ' + args[0] )
					usedLFOs.append( lfo )
				elif opcode in [ 'clr' ]:
					line = 'e.' + opcode + '();'
				elif opcode.endswith( ':' ):
					line = 'l' + opcode
				else:
					raise Exception( 'unknown opcode: ' + opcode )
				code.append( [ number, line + comments, pacc ] )
				number += 1
		else:
				code.append( [ -1, comments, False ] )

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
	print( '    uint32_t del = state->del;' )
if anyPacc:
	print( '    float pacc;' )

for i in range( len( code ) ):
	x = code[i]
	if x[0] in usedLabels:
		print( 'l' + str( x[0] ) + ':' )
	if i < len( code ) - 1:
		if code[i+1][2]:
			print( '    pacc = e.acc;' )
	print( '    ' + x[1] )

for lfo in [ 'rmp0', 'rmp1', 'sin0', 'sin1' ]:
	if lfo in usedLFOs:
		print( f'    e.update_{lfo}();' )

print( '}' )
