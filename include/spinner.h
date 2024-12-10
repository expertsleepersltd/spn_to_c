/*
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
*/

#ifndef SPINNER_H_
#define SPINNER_H_

#include <three_pot_state.h>
#include <algorithm>

namespace _three_pot
{

inline __attribute__((always_inline))	float Sin01( float t )
{
	t = std::max( -t, std::min( 1.0f - t, t - 0.5f ) );

	float t2 = t  * t;
	float t3 = t  * t2;
	float t5 = t2 * t3;
	float t7 = t2 * t5;
	float t9 = t2 * t7;

	float r = t  * (float)(-6.283185307179586);
	r =   r + t3 * (float)(248.0502134423985 * 0.16666657);
	r =   r + t5 * (float)(9792.629913129005 * -8.3330255e-003);
	r =   r + t7 * (float)(386597.5331554293 * 1.9807414e-004);
	r =   r + t9 * (float)(15262258.85872445 * -2.601887e-006);

	return r;
}

inline __attribute__((always_inline)) float f_abs( float x )
{
#ifdef __arm__
    float r;
    asm( "VABS.F32 %0, %1" : "=t" (r) : "t" (x) );
    return r;
#else
    return ( x < 0.0f ) ? (-x) : x;
#endif
}

enum
{
	cho_cos = 1,
	cho_reg = 2,
	cho_compc = 4,
	cho_compa = 8,
	cho_rptr2 = 16,
	cho_na = 32,
};

enum _cho_lfo
{
	cho_sin0,
	cho_sin1,
	cho_rmp0,
	cho_rmp1,
};

class _spinner
{
public:
	_spinner( _three_pot::_state* state_ ) : state( state_ ), acc( 0 ) {}

	_three_pot::_state*	state;

	float 	acc;
	float	lr;
	float	lfo;

	inline __attribute__((always_inline))	void	cho_rda( _cho_lfo which, uint32_t flags, uint32_t offset )
	{
		float lfo_in =  ( which == cho_sin0 ) ? ( ( flags & cho_cos ) ? state->cos0 : state->sin0 ) : (
						( which == cho_sin1 ) ? ( ( flags & cho_cos ) ? state->cos1 : state->sin1 ) : (
						( which == cho_rmp0 ) ? state->rmp0 : state->rmp1 ) );
		float range  =  ( which == cho_sin0 ) ? state->sin0_range * 8192.0f : (
						( which == cho_sin1 ) ? state->sin1_range * 8192.0f : (
						( which == cho_rmp0 ) ? state->rmp0_range : state->rmp1_range ) );
		if ( flags & cho_reg )
			lfo = lfo_in;
		float v = lfo;
		if ( flags & cho_rptr2 )
		{
			v += 0.5f;
			if ( v >= 1.0f )
				v -= 1.0f;
		}
		if ( flags & cho_compa )
			v = -v;
		uint32_t index;
		float c;
		if ( flags & cho_na )
		{
			index = offset;
			c = std::min( v, 1.0f - v );
			c = std::max( 0.0f, std::min( 1.0f, 4 * c - 0.5f ) );
		}
		else
		{
			float addr = v * range + offset;
			index = addr;
			c = addr - index;
		}
		lr = state->delay_ptr[ ( index + 32768 ) & 32767 ];
		if ( flags & cho_compc )
			c = 1 - c;
		acc += lr * c;
	}
	inline __attribute__((always_inline))	void	cho_rdal( float a )
	{
		acc = a;
	}
	inline __attribute__((always_inline))	void	cho_sof( _cho_lfo which, uint32_t flags, float b )
	{
		float lfo_in =  ( which == cho_sin0 ) ? ( ( flags & cho_cos ) ? state->cos0 : state->sin0 ) : (
						( which == cho_sin1 ) ? ( ( flags & cho_cos ) ? state->cos1 : state->sin1 ) : (
						( which == cho_rmp0 ) ? state->rmp0 : state->rmp1 ) );
		if ( flags & cho_reg )
			lfo = lfo_in;
		float v = lfo;
		if ( flags & cho_na )
		{
			v = std::min( v, 1.0f - v );
			v = std::max( 0.0f, std::min( 1.0f, 4 * v - 0.5f ) );
		}
		if ( flags & cho_compc )
			v = 1 - v;
		acc = v * acc + b;
	}
	inline __attribute__((always_inline))	void	clr(void)
	{
		acc = 0;
	}
	inline __attribute__((always_inline))	void	exp( float a, float b )
	{
		acc = state->exp2( acc * 16 ) * a + b;
	}
	inline __attribute__((always_inline))	void	log( float a, float b )
	{
		acc = a * state->log2( f_abs( acc ) ) * (1.0f/16) + b;
	}
	inline __attribute__((always_inline))	void	maxx( float a, float b )
	{
		acc = std::max( f_abs( acc ), f_abs( a * b ) );
	}
	inline __attribute__((always_inline))	void	mulx( float a )
	{
		acc *= a;
	}
	inline __attribute__((always_inline))	void	rda( float a, float b )
	{
		lr = a;
		acc += a * b;
	}
	inline __attribute__((always_inline))	void	rdax( float a, float b )
	{
		acc += a * b;
	}
	inline __attribute__((always_inline))	void	rdfx( float a, float b )
	{
		acc = a + ( acc - a ) * b;
	}
	inline __attribute__((always_inline))	void	rmpa( float a )
	{
		uint32_t index = (uint32_t)( state->addr_ptr * (1<<15) ) & 0x7fff;
		lr = state->delay_ptr[ ( index + state->del ) & 32767 ];
		acc += a * lr;
	}
	inline __attribute__((always_inline))	void	sof( float a, float b )
	{
		acc = a * acc + b;
	}
	inline __attribute__((always_inline))	void 	wldr( int n, float f, float a )
	{
		if ( n )
		{
			state->rmp1_rate = f;
			state->rmp1_range = a;
			state->rmp1_rateMul = -1.0f/a;
		}
		else
		{
			state->rmp0_rate = f;
			state->rmp0_range = a;
			state->rmp0_rateMul = -1.0f/a;
		}
	}
	inline __attribute__((always_inline))	void 	wlds( int n, float f, float a )
	{
		f /= 511.0f;
		a /= 32767.0f;
		if ( n )
		{
			state->sin1_rate = f;
			state->sin1_range = a;
		}
		else
		{
			state->sin0_rate = f;
			state->sin0_range = a;
		}
	}
	inline __attribute__((always_inline))	void	wra( float& a, float b )
	{
		a = acc;
		acc *= b;
	}
	inline __attribute__((always_inline))	void	wrap( float& a, float b )
	{
		a = acc;
		acc = acc * b + lr;
	}
	inline __attribute__((always_inline))	void	wrax( float& a, float b )
	{
		a = acc;
		acc *= b;
	}
	inline __attribute__((always_inline))	void	wrhx( float& a, float b, float pacc )
	{
		a = acc;
		acc = pacc + acc * b;
	}
	inline __attribute__((always_inline))	void	wrlx( float& a, float b, float pacc )
	{
		a = acc;
		acc = ( pacc - acc ) * b + pacc;
	}
	inline __attribute__((always_inline))	void	absa(void)
	{
		acc = f_abs( acc );
	}
	inline __attribute__((always_inline))	void	ldax( float a )
	{
		acc = a;
	}
	
	inline __attribute__((always_inline))	uint32_t	to_bits( float x )
	{
		return (uint32_t)( x * (1<<23) ) & 0xffffff;
	}
	inline __attribute__((always_inline))	float		from_bits( uint32_t x )
	{
		int32_t v = x;
		v = ( v << 8 ) >> 8;
		return v * (1.0f/(1<<23));
	}
	inline __attribute__((always_inline))	void	bitwise_and( uint32_t a )
	{
		uint32_t x = to_bits( acc );
		acc = from_bits( x & a );
	}
	inline __attribute__((always_inline))	void	bitwise_or( uint32_t a )
	{
		uint32_t x = to_bits( acc );
		acc = from_bits( x | a );
	}

	inline __attribute__((always_inline))	void	update_rmp0(void)
	{
	    state->rmp0 += state->rmp0_rate * state->rmp0_rateMul;
	    while ( state->rmp0 >= 1 )
	    	state->rmp0 -= 1;
	    while ( state->rmp0 < 0 )
	    	state->rmp0 += 1;
	}
	inline __attribute__((always_inline))	void	update_rmp1(void)
	{
	    state->rmp1 += state->rmp1_rate * state->rmp1_rateMul;
	    while ( state->rmp1 >= 1 )
	    	state->rmp1 -= 1;
	    while ( state->rmp1 < 0 )
	    	state->rmp1 += 1;
	}
	inline __attribute__((always_inline))	void	update_sin0(void)
	{
	    state->sin0_t += state->sin0_rate * state->sin_rateMul;
	    while ( state->sin0_t >= 1 )
	    	state->sin0_t -= 1;
	    while ( state->sin0_t < 0 )
	    	state->sin0_t += 1;
	    float s = Sin01( state->sin0_t );
	    float c = Sin01( state->sin0_t + 0.25f );
	    state->sin0 = s;
	    state->cos0 = c;
	}
	inline __attribute__((always_inline))	void	update_sin1(void)
	{
	    state->sin1_t += state->sin1_rate * state->sin_rateMul;
	    while ( state->sin1_t >= 1 )
	    	state->sin1_t -= 1;
	    while ( state->sin1_t < 0 )
	    	state->sin1_t += 1;
	    float s = Sin01( state->sin1_t );
	    float c = Sin01( state->sin1_t + 0.25f );
	    state->sin1 = s;
	    state->cos1 = c;
	}
};

}

#endif // SPINNER_H_
