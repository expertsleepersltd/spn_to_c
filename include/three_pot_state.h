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
	
	uint32_t 		del;
	uint32_t		run;
	float			sin_rateMul;
	
	float 			pot0;
	float 			pot1;
	float 			pot2;
	
	float			adcl;
	float			adcr;
	float			dacl;
	float			dacr;

	float			rmp0;
	float			rmp0_rate;
	float			rmp0_range;
	float			rmp0_rateMul;
	float			rmp1;
	float			rmp1_rate;
	float			rmp1_range;
	float			rmp1_rateMul;
	float			sin0;
	float			cos0;
	float			sin0_t;
	float			sin0_rate;
	float			sin0_range;
	float			sin1;
	float			cos1;
	float			sin1_t;
	float			sin1_rate;
	float			sin1_range;

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
	
	float			addr_ptr;
};

typedef void (process)( _state* state );

};	// namespace _three_pot

#endif // THREE_POT_STATE_H_
