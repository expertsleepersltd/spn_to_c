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

#ifndef THREE_POT_STATE_H_
#define THREE_POT_STATE_H_

#include <stdint.h>

namespace _three_pot
{

struct _state
{
	float*			delay_ptr;

	float			(*exp2)(float);
	float			(*log2)(float);
	
	uint32_t 		downcounter;
	uint32_t		run;
	float			sin_rateMul;
	
	union
	{
		struct
		{
			float			sin0_rate;
			float			sin0_range;
			float			sin1_rate;
			float			sin1_range;
			float			rmp0_rate;
			float			rmp0_range;
			float			rmp1_rate;
			float			rmp1_range;
			float			unused[8];
			float 			pot0;
			float 			pot1;
			float 			pot2;
			float			unused2;
			float			adcl;
			float			adcr;
			float			dacl;
			float			dacr;
			float			addr_ptr;
			float			unused3[7];
			float			reg0;
			float			reg1;
			float			reg2;
			float			reg3;
			float			reg4;
			float			reg5;
			float			reg6;
			float			reg7;
			float			reg8;
			float			reg9;
			float			reg10;
			float			reg11;
			float			reg12;
			float			reg13;
			float			reg14;
			float			reg15;
			float			reg16;
			float			reg17;
			float			reg18;
			float			reg19;
			float			reg20;
			float			reg21;
			float			reg22;
			float			reg23;
			float			reg24;
			float			reg25;
			float			reg26;
			float			reg27;
			float			reg28;
			float			reg29;
			float			reg30;
			float			reg31;
		};
		float		registers[64];
	};
	
	float			rmp0;
	float			rmp1;
	float			sin0;
	float			cos0;
	float			sin0_t;
	float			sin1;
	float			cos1;
	float			sin1_t;
};

typedef void (process)( _state* state );

};	// namespace _three_pot

#endif // THREE_POT_STATE_H_
