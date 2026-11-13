<!-- Copy of the proposal submitted to Prof. Dion Antao (Google Doc 15-BWKmpDC7ilC62ebvVjaLJG_joX_vqysZ8ISMHtEko), saved 2026-11-07. Do not edit; this is the reference for scope. -->

# **Second-Law Analysis and Constrained Optimization of a Liquid-Cooled Cold Plate for a 1 kW Electronic Heat Source**

MEEN 615: Advanced Engineering Thermodynamics,   
Fall 2026, Project Proposal  
Group: Sai Krishna Kommineni, Suneel Kumar, Sam        

Instructor: Prof. Dion Antao 

## **Abstract**

AI processors now dissipate close to 1 kW from a die of about 30 mm by 30 mm, so data centers are moving to direct-to-chip liquid cooling. Cold plates are usually sized by minimizing thermal resistance, but that criterion always favors more flow because it ignores the pump work needed to push water through narrow channels. In this project we will use the second law to find how much flow, and what channel geometry, is worth it.

We will build a reduced-order model of a water-cooled copper microchannel cold plate in Python and validate it against the experiments of Qu and Mudawar (2002). Entropy generation will be calculated for the cold plate plus the return of the coolant to its inlet temperature, and converted to lost work with the Gouy-Stodola theorem. Channel width, fin thickness and flow rate will be optimized to minimize lost work while keeping the device below 90 °C and the pressure drop below 50 kPa, and compared with the minimum thermal resistance design. We will then vary the inlet temperature from 20 to 50 °C to see when the temperature limit takes over and how much exergy the outlet water carries. A first estimate for 0.2 mm channels gives an optimum flow of about 4 to 5 L/min.

## **Introduction and problem statement**

Microchannel heat sinks remove high heat fluxes with a small temperature rise (Tuckerman and Pease, 1981), but narrow channels and high flow increase the pressure drop. Two losses compete: heat crossing a finite temperature difference, which more flow reduces, and viscous friction, which more flow increases. Thermal resistance only sees the first. Bejan's entropy generation minimization puts both on the same scale and has been applied to microchannel heat sinks (Khan et al., 2009).

Pumping power is only a few watts for one chip, but it grows with the square of the flow in laminar channels, and dozens of cold plates in a rack share one pump loop. More flow also cannot fix a bad geometry, since it only reduces one of the four thermal resistances between chip and water. Data centers also want warmer coolant to save chiller energy (ASHRAE TC 9.9), which reduces the chip's margin.

**Setup.** We picked the inputs to represent a current AI accelerator in a typical liquid-cooled server rather than one specific product. The heat source is 1000 W spread uniformly over 30 x 30 mm (about 110 W/cm2), which is the power class of current AI accelerators; uniform flux keeps the model one-dimensional. The cold plate is copper (k \= 390 W/m·K), the usual material for cold plates, with 3 mm fins and a 1 mm base, which are common for skived-fin designs. We fix the fin height so that the optimization has three variables. The junction plus TIM resistance is fixed at 0.02 K/W, a typical value for large packages that adds about 20 K at full power, and we vary it in the sensitivity study.

The water enters at 30 °C, which falls in ASHRAE's W32 class for facility water, and the inlet temperature study covers 20 to 50 °C (roughly W17 to W45). Channel widths of 0.1 to 1.0 mm and fin thicknesses of 0.1 to 0.5 mm cover what skiving and micromachining can produce, and flows of 0.5 to 12 L/min go from typical industry practice (about 1 to 2 L/min per kW) up to the laminar limit of the narrowest channels. The objective is to minimize lost work T0Sgen, with T0 \= 25 °C as the reference environment. The constraints are a device temperature of 90 °C, close to where GPUs start to throttle; a pressure drop of 50 kPa, which we assume as the budget for one cold plate in a rack loop; and laminar flow, since the correlations we use are only valid for laminar flow.

The main question we want to answer is: how much coolant flow is thermodynamically worthwhile before the extra friction losses outweigh the reduction in heat-transfer irreversibility, and how do the channel geometry, the device temperature limit and the coolant inlet temperature change that optimum?

## **Objectives**

> 1. Build a model that gives device temperature, pressure drop and pump power for any channel width, fin thickness and flow rate.  
> 2. Validate it against the measured data of Qu and Mudawar (2002).  
> 3. Calculate entropy generation, split it into its sources, and express it as lost work.  
> 4. Find the flow and geometry that minimize lost work under the constraints and compare with the minimum thermal resistance design.  
> 5. Find the highest inlet temperature at which the optimum is still feasible, and the exergy of the outlet water.

## **Approach**

The model is a 1D thermal resistance network with the TIM, base conduction, fin-array convection and the coolant temperature rise in series. Heat transfer and friction use the fully developed laminar Nusselt number and fRe for rectangular ducts (Shah and London), the fins use the standard fin efficiency, and water properties come from CoolProp. The hottest device point is above the outlet:

*Tdev \= Tin \+ Q \[1/(ṁcp) \+ 1/(hAeff) \+ tb/(ksWL) \+ RTIM\]*

The part that needs some care is the control volume for the second-law analysis. If it contains only the cold plate, more flow just makes the water colder, entropy generation slightly increases, and there is no optimum. What it misses is the warm water being cooled back to the inlet temperature in the CDU. We therefore include the cold plate and the return to Tin, so heat Q enters at the mean base temperature Ts and Q plus all pump work leaves at Tin:

*Sgen \= Q (1/Tin − 1/Ts) \+ Wpump/Tin,     Xlost \= T0Sgen*

The first term splits into a coolant-warming loss that falls as 1/V and a base-to-coolant loss that is nearly independent of flow, while pumping grows as V2, so the optimum flow is roughly V\* \= (B/2C)1/3. We will check the numerical optimum against this estimate. The studies are a flow sweep at the reference geometry (0.2 mm channels and fins), a constrained optimization of all three variables (grid sweep, then SciPy SLSQP) compared with the minimum thermal resistance design, an inlet temperature sweep from 20 to 50 °C, and a short sensitivity check on the TIM resistance and pump efficiency.

## **Validation**

We will run the model at the test conditions of Qu and Mudawar (2002), a copper heat sink with 21 channels of 231 µm by 713 µm, and compare against their measured pressure drop and temperatures, aiming for errors within about 10 to 15%. Their channels are short compared with the thermal entry length, so if the error is too large we will switch to a developing-flow Nusselt correlation. As a second-law check, entropy generation must be positive everywhere and, for laminar flow, the coolant-warming loss should be about twice the pumping loss at the optimum.

## **Resources and timeline**

Everything is done in Python (NumPy, SciPy, Matplotlib) with CoolProp on a standard laptop, with the code on GitHub, so no lab equipment or paid software is needed. The model and tests will be done by Nov 3, validation and the second-law module by Nov 12, the studies by Nov 22, and the final report and code by Dec 3\. The main assumptions are steady single-phase laminar flow, uniform heat flux and equal flow in all channels.

**Below is the Github Link which contains files of this project and we will update this every week.** 

**https\://github.com/krishna24558/coldplate-egm**

## **References**

> 1. W. Qu and I. Mudawar, "Experimental and numerical study of pressure drop and heat transfer in a single-phase micro-channel heat sink," Int. J. Heat Mass Transfer, vol. 45, pp. 2549-2565, 2002\.  
> 2. D. B. Tuckerman and R. F. W. Pease, "High-performance heat sinking for VLSI," IEEE Electron Device Lett., vol. EDL-2, no. 5, pp. 126-129, 1981\.  
> 3. A. Bejan, Entropy Generation Minimization. Boca Raton, FL: CRC Press, 1996\.  
> 4. W. A. Khan, M. M. Yovanovich and J. R. Culham, "Optimization of microchannel heat sinks using entropy generation minimization method," IEEE Trans. Compon. Packag. Technol., 2009, doi:10.1109/TCAPT.2009.2022586.  
> 5. ASHRAE TC 9.9, Thermal Guidelines for Data Processing Environments, 5th ed. Atlanta, GA: ASHRAE, 2021\.  
> 6. R. K. Shah and A. L. London, Laminar Flow Forced Convection in Ducts. New York: Academic Press, 1978\.  
> 7. T. L. Bergman, A. S. Lavine, F. P. Incropera and D. P. DeWitt, Fundamentals of Heat and Mass Transfer, 7th ed. Wiley, 2011\.  
> 8. I. H. Bell et al., "Pure and pseudo-pure fluid thermophysical property evaluation and the open-source thermophysical property library CoolProp," Ind. Eng. Chem. Res., vol. 53, pp. 2498-2508, 2014\.