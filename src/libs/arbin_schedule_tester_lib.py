# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 12:12:23 2020

@author: asbjornu
"""

import re
import time
import operator
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from bokeh.io import output_file, show
from bokeh.layouts import gridplot
from bokeh.plotting import figure
from bokeh.models import NumeralTickFormatter
import bokeh.palettes as palettes
import io


class ResponseFunction:

    def __init__(self, cell_type='half_cell'):
        self.func = None
        self.cell_type = cell_type
        self.init_pot_to_soc()
        self.fast_soc_to_pot_array = []
        self.init_fast_soc_to_pot()

    def _direct_soc_to_pot(self, soc):
        # pot = 0.0005/SOC -4.76*np.power(SOC,6) + 9.34*np.power(SOC,5) - 1.8*np.power(SOC,4) - 7.13*np.power(SOC,3) +
        # 5.8*np.power(SOC,2) - 1.94*SOC + 0.82 + (-(0.2/(1.0001-np.power(SOC,1000))))
        
        if self.cell_type == 'full_cell_LFP_nadadadadadada':
            # return (3.2-0.2*soc - 200*np.power(soc-0.46, 9) - 5e5*np.power(soc-0.483624, 21) - 6e30*np.power(soc-0.5, 101))
            pass
        else:
            return 0.0000002975 * np.power(soc + 0.005, -3) - 4.76 * np.power(soc, 6) + 9.34 * np.power(soc, 5) - \
                    1.8 * np.power(soc, 4) - 7.13 * np.power(soc, 3) + 5.8 * np.power(soc, 2) - 1.94 * soc + 0.82 - \
                    0.2 - (0.0000000001 / (np.power((1.005 - soc), 4)))
        # return  pot.clip(0.0, 3.0)

    def init_pot_to_soc(self):
        #        x = [i*1./100000 for i in range(1,100001)]
        x = np.linspace(0, 100000, 100000) / 100000
        y = self._direct_soc_to_pot(x)
        # import matplotlib.pyplot as plt
        # plt.plot(x, y)
        self.func = interp1d(y, x)

    def init_fast_soc_to_pot(self):
        x = np.linspace(-499, 100500, 100999) / 100000
        self.fast_soc_to_pot_array = self._direct_soc_to_pot(x)

    def pot_to_soc(self, potential):
        return self.func(potential)

    def fast_soc_to_pot(self, soc):
        #if 'full_cell' in self.cell_type:
        #    soc = -soc

        return_value = self.fast_soc_to_pot_array[int(np.max([np.min([soc * 100000 + 498, 100498]), 0]))]


        if 'full_cell' in self.cell_type:
            if 'NMC' in self.cell_type:
                if return_value > 2.25:
                    return_value = 2.25
                elif return_value < -3:
                    return_value = -3
                return 4.5 - return_value * 2

            elif 'LFP' in self.cell_type:
                if return_value > 3.6:
                    return_value = 3.6
                elif return_value < -3.6:
                    return_value = -3.6
                return 3.6 - return_value

            else:
                if soc <= 0.001:
                    return 0
                elif soc >= 0.999:
                    return 8
                if return_value > 2.0:
                    return_value = 2.0
                elif return_value < -3:
                    return_value = -3
                return 3.5 - return_value

        else:
            if 'XNO' in self.cell_type:
                if return_value > 3:
                    return_value = 3
                elif return_value < 0:
                    return_value = 0
                return 1 + return_value*2
            else:
                if return_value > 3:
                    return_value = 3
                elif return_value < 0:
                    return_value = 0
                return return_value


class Tester:
    def __init__(self):
        self.schedule = Schedule()
        self.cell = None
        self.output = None
        self.inferred_cell_type_from_schedule = None

    def _infer_cell_type_from_schedule(self, schedule):
        half_cell_weight = 0
        half_cell_XNO_weight = 0
        full_cell_LFP_weight = 0
        full_cell_NMC_weight = 0
        full_cell_weight = 0

        for step in schedule.step_info_table:
            for limit in step[1]:
                if limit['m_bStepLimit'] == '1' and limit['Equation0_szLeft'] == 'PV_CHAN_Voltage':
                    if '<' in limit['Equation0_szCompareSign']:
                        if float(limit['Equation0_szRight']) < 0.5:
                            half_cell_weight += 1
                        elif float(limit['Equation0_szRight']) < 1.8:
                            half_cell_XNO_weight += 1
                        elif float(limit['Equation0_szRight']) < 2.6:
                            full_cell_LFP_weight += 1
                            full_cell_NMC_weight += 1
                        else:
                            full_cell_NMC_weight += 1
                    elif '>' in limit['Equation0_szCompareSign']:
                        if float(limit['Equation0_szRight']) < 1.6:
                            half_cell_weight += 1
                        elif float(limit['Equation0_szRight']) < 2.8:
                            half_cell_XNO_weight += 1
                        elif float(limit['Equation0_szRight']) < 3.8:
                            full_cell_LFP_weight += 1
                        elif float(limit['Equation0_szRight']) < 4.6:
                            full_cell_NMC_weight += 1
                        else:
                            full_cell_weight += 5

        print("Cell type inferrence from schedule:")
        print("Half cell:", half_cell_weight)
        print("Full cell LFP:", full_cell_LFP_weight)
        print("Full cell NMC:", full_cell_NMC_weight)
        
        if half_cell_weight > max(half_cell_XNO_weight, full_cell_NMC_weight, full_cell_LFP_weight, full_cell_weight):
            return 'half_cell'
        if half_cell_XNO_weight > max(full_cell_NMC_weight, full_cell_LFP_weight, full_cell_weight):
            return 'half_cell_XNO'
        elif full_cell_LFP_weight > max(full_cell_NMC_weight, full_cell_weight):
            return 'full_cell_LFP'
        elif full_cell_NMC_weight > full_cell_weight:
            return 'full_cell_NMC'
        else: 
            return 'full_cell'  

    def set_schedule(self, filename = None, schedule_lines = None):
        if filename is not None:
            with open(filename) as f:
                self.schedule.read_schedule(f.readlines())
        elif schedule_lines is not None:
            self.schedule.read_schedule(schedule_lines)

        self.schedule.build_schedule()
        self.inferred_cell_type_from_schedule = self._infer_cell_type_from_schedule(self.schedule)

    def build_cell(self, mass=0.002, specific_capacity=1.000, delta_time=1, cell_type=None, soc_length=10):
        if cell_type == None:
            cell_type = self.inferred_cell_type_from_schedule            
        self.cell = Cell(delta_time, cell_type, mass, specific_capacity, soc_length=soc_length)

    def run_test(self, max_cycles=100, progress_bar = None, timeout = None):
        self.schedule.run_cell(self.cell, max_cycles, progress_bar=progress_bar, timeout = timeout)

    def prepare_output(self):
        self.output = pd.DataFrame(self.cell.log, columns=[*self.cell.current_state.keys()])

    def make_overview_bokeh(self, filename=None, fig_width=1900, fig_height=960, line_width=1, line_alpha=1, show_plot=True,
                            output_excel=False, normalize=False, vertical_stack=False):
        if filename is not None:
            output_file(filename)
        
        if self.output is None:
            self.prepare_output()

        if output_excel:
            self.output.to_excel(filename.with_suffix(".xlsx"))

        x = self.output.PV_CHAN_Test_Time
        v = self.output.PV_CHAN_Voltage

        cc = self.output.PV_CHAN_Charge_Capacity

        dc = self.output.PV_CHAN_Discharge_Capacity

        c = self.output.PV_CHAN_Current
        
        if normalize:
            cc = cc/self.cell.nominalCapacity
            dc = dc/self.cell.nominalCapacity
            c = c/self.cell.nominalCapacity

        ci = self.output.PV_CHAN_Cycle_Index
        si = self.output.PV_CHAN_Step_Index
        c1 = self.output.TC_Counter1
        c2 = self.output.TC_Counter2
        c3 = self.output.TC_Counter3
        c4 = self.output.TC_Counter4

        width = int(fig_width / 2)
        height = int(fig_height / 2)
        colors = palettes.Category10_10

        s11 = figure(width=width, height=height, title="Voltage")
        for data, name, color in zip([v], ["Voltage"], colors):
            s11.line(x, data, legend_label=name, line_width=line_width, line_color=color, line_alpha=line_alpha, )
        s11.legend.location = "top_right"
        s11.legend.click_policy = "hide"
        s11.legend.items = []

        s12 = figure(width=width, height=height, x_range=s11.x_range, title="Capacity")
        for data, name, color in zip([cc, dc], ["Charge Capacity", "Discharge Capacity"], colors):
            s12.line(x, data, line_width=line_width, line_color=color, line_alpha=line_alpha, legend_label=name)
        s12.legend.location = "top_right"
        s12.legend.click_policy = "hide"

        s21 = figure(width=width, height=height, x_range=s11.x_range, title="Current")
        for data, name, color in zip([c], ["Current"], colors):
            s21.line(x, data, line_width=line_width, line_color=color, line_alpha=line_alpha, legend_label=name)
        s21.legend.location = "top_left"
        s21.legend.click_policy = "hide"
        s21.legend.items = []

        s22 = figure(width=width, height=height, x_range=s11.x_range, title="Counters")
        for data, name, color in zip([ci, si, c1, c2, c3, c4],
                                     ["Cycle index", "Step index", "TC_Counter1", "TC_Counter2", "TC_Counter3",
                                      "TC_Counter4"], colors):
            s22.line(x, data, line_width=line_width, line_color=color, line_alpha=line_alpha, legend_label=name)
        s22.legend.location = "top_left"
        s22.legend.click_policy = "hide"

        if normalize:
            s12.title = r"Capacity [% of nominal]"
            s21.title = "Current [C-rate]"

        if vertical_stack:
            p = gridplot([[s11], [s21], [s12], [s22]])
        else:
            p = gridplot([[s11, s12], [s21, s22]])
    
        if show_plot:
            show(p)
        
        self.plot = p
    
        return p
    

class Schedule:
    def __init__(self):
        self.steps = []
        self.formulas = dict()
        self.step_info_table = None
        self.formula_info_list = None
        self.current_step = None
        self.progress_bar = None

    def read_schedule(self, schedule_lines):
            self.step_info_table = []
            self.formula_info_list = []
            level = 0

            for line in schedule_lines:
                # print(line)
                try:
                    p = re.match(r'^\[Schedule_Step([0-9]*)_Limit([0-9]*)]$', line)
                    if p is not None:
                        level = 'limit'
                        self.step_info_table[-1][1].append(dict())

                    p = re.match(r'^\[Schedule_Step([0-9]*)]$', line)
                    if p is not None:
                        level = 'step'
                        self.step_info_table.append([dict(), []])
                        self.step_info_table[-1][0]["StepIndex"] = int(p.group(1)) + 1

                    p = re.match(r'^\[Schedule_Formula([0-9]*)]$', line)
                    if p is not None:
                        level = 'formula'
                        self.formula_info_list.append(dict())
                        self.formula_info_list[-1]["FormulaIndex"] = int(p.group(1)) + 1

                    p = re.match(r'^([^=\[]*)=(.*)$', line)
                    if p is not None:
                        p = re.match(r'^([^=]*)=(.*)$', line)
                        key = p.group(1)
                        value = p.group(2)

                        if level == 'step':
                            self.step_info_table[-1][0][key] = value
                        elif level == 'limit':
                            self.step_info_table[-1][1][-1][key] = value
                        elif level == 'formula':
                            self.formula_info_list[-1][key] = value

                except UnicodeDecodeError as e:
                    print(f"error in line:\n {f}")
                    print(e)

    def build_schedule(self):
        for formulaInfo in self.formula_info_list:
            self.formulas[formulaInfo['m_szLabel']] = Formula(formulaInfo)

        for stepinfo in self.step_info_table:
            self.steps.append(Step(stepinfo, self.formulas))

    def run_cell(self, cell, max_cycles, progress_bar = None, timeout = 1e100):
        self.current_step = self.steps[0]
        self.update_formula_values_and_limits(cell)

        go_to = self.current_step.execute(cell)

        while not (
                go_to == "End Test" or (go_to == "Next Step" and self.current_step is self.steps[-1]) or
                cell.current_state["PV_CHAN_Cycle_Index"] > max_cycles or
                cell.current_state["PV_CHAN_Test_Time"] > timeout):
            if go_to == "Next Step":
                self.current_step = self.steps[self.steps.index(self.current_step) + 1]
            else:
                for step in self.steps:
                    if step.stepName == go_to:
                        self.current_step = step

            self.update_formula_values_and_limits(cell)
            
            if progress_bar is not None:
                progress_bar.progress(1.0 * cell.current_state["PV_CHAN_Cycle_Index"] / max_cycles, f"Schedule running... (Cycle {cell.current_state['PV_CHAN_Cycle_Index']}/{max_cycles}, step {cell.current_state['PV_CHAN_Step_Index']})")

            go_to = self.current_step.execute(cell)


    def update_formula_values_and_limits(self, cell):
        for formula in self.formulas.values():
            formula.update(cell.current_state)

        for step in self.steps:
            for limit in step.limits:
                limit.update()


class Formula:
    def __init__(self, formula_info):
        self.warned = False
        self.formula_name = formula_info["m_szLabel"]
        self.expression = formula_info["m_szExpression"]
        self.expression = self.expression.replace("EXP", "np.exp")

        for variable in ["TC_Counter1", "TC_Counter2", "TC_Counter3", "TC_Counter4", "PV_CHAN_Cycle_Index",
                         "PV_CHAN_Step_Index", "MV_Mass", "MV_SpecificCapacity"]:
            self.expression = self.expression.replace(variable, "current_state['" + variable + "']")

        self.value = 0

    def update(self, current_state):
        try:
            self.value = eval(self.expression)
        except NameError as e:
            self.value = 0
            if not self.warned:
                print(f"Formula eval failed for {self.formula_name}, "
                      f"with expression {self.expression}. Defaulting to 0.")
                print(e)
                self.warned = True

    def get_value(self):
        return self.value


class Step:
    def __init__(self, step_info, formulas):
        self.limits = []
        self.log_limits = []
        self.stepInfo = step_info
        self.formulas = formulas
        self.stepInfo = step_info[0]

        for limit_info in step_info[1]:
            if limit_info['m_bStepLimit'] == '1':
                self.limits.append(Limit(limit_info, formulas))
            elif limit_info['m_bLogDataLimit'] == '1':
                self.log_limits.append(Limit(limit_info, formulas))

        self.stepName = self.stepInfo['m_szLabel']
        self.stepType = self.stepInfo['m_szStepCtrlType']
        self.stepIndex = self.stepInfo["StepIndex"]

        print('')
        print("Step index: ", self.stepIndex)
        print("Step name: ", self.stepName)
        print("Step type: ", self.stepType)

        try:
            if self.stepType == 'C-Rate':
                try:
                    self.cRate = float(self.stepInfo['m_szCtrlValue'])
                except ValueError:
                    self.cRate = self.stepInfo['m_szCtrlValue']
                self.current = 'null'
                print('C-rate: ', self.cRate)
            if self.stepType == 'Current(A)':
                self.cRate = 'null'
                self.current = float(self.stepInfo['m_szCtrlValue'])
                print('Current: ', self.current)
            elif self.stepType == 'Voltage(V)':
                self.cRate = 'null'
                self.current = 'floating'
                self.voltage = float(self.stepInfo['m_szCtrlValue'])
            elif self.stepType == 'Rest':
                self.cRate = 0
            elif self.stepType == 'Set Variable(s)':
                if self.stepInfo['m_szCtrlValue'] != "":
                    self.zero = int(self.stepInfo['m_szCtrlValue'])
                else:
                    self.zero = 0

                if self.stepInfo['m_szExtCtrlValue1'] != "":
                    self.increment = int(self.stepInfo['m_szExtCtrlValue1'])
                else:
                    self.increment = 0

                if self.stepInfo['m_szExtCtrlValue2'] != "":
                    self.decrement = int(self.stepInfo['m_szExtCtrlValue2'])
                else:
                    self.decrement = 0
            else:
                print("Step-type cannot be determined for step", self.stepIndex)

        except Exception as e:
            print("WARNING! Error in interpretation of step", self.stepIndex)
            raise e

    def execute(self, cell):

        cell.set_step_index(self.stepIndex)
        cell.zero_step_time()

        if self.stepType == "C-Rate":
            #            print("Running step number", self.stepIndex, "which is a step of type", self.stepType)
            running = True
            go_to = "End Test"
            while running:
                cell.increment_time()
                if type(self.cRate) == float:
                    cell.increment_current(crate=self.cRate)
                elif type(self.cRate) == str:
                    cell.increment_current(crate=self.formulas[self.cRate].get_value())

                cell.update_cell_voltage()
                #                cell.logState()

                is_triggered, go_to = self.check_limits(cell.current_state)

                if is_triggered:
                    cell.log_state()
                    running = False
                elif self.check_log_limits(cell.current_state):
                    cell.log_state()

            return go_to

        elif self.stepType == "Current(A)":
            #            print("Running step number", self.stepIndex, "which is a step of type", self.stepType)
            go_to = "End Test"
            running = True
            while running:
                cell.increment_time()
                cell.increment_current(current=self.current)
                cell.update_cell_voltage()
                #                cell.logState()

                is_triggered, go_to = self.check_limits(cell.current_state)

                if is_triggered:
                    cell.log_state()
                    running = False
                elif self.check_log_limits(cell.current_state):
                    cell.log_state()

            return go_to

        elif self.stepType == "Voltage(V)":
            go_to = "End Test"
            running = True
            while running:
                cell.increment_time()
                cell.increment_current(current=self.current, constant_voltage=self.voltage)
                cell.update_cell_voltage()

                is_triggered, go_to = self.check_limits(cell.current_state)

                if is_triggered:
                    cell.log_state()
                    running = False
                elif self.check_log_limits(cell.current_state):
                    cell.log_state()

            return go_to

        elif self.stepType == "Rest":
            #            print("Running step number", self.stepIndex, "which is a step of type", self.stepType)
            go_to = "End Test"
            running = True
            while running:
                cell.increment_time()
                cell.increment_current(crate=0)
                cell.update_cell_voltage()
                #                cell.logState()
                if self.check_log_limits(cell.current_state):
                    cell.log_state()

                is_triggered, go_to = self.check_limits(cell.current_state)
                if is_triggered:
                    running = False

            return go_to

        elif self.stepType == "Internal Resistance":
            #            print("Running step number", self.stepIndex, "which is a step of type", self.stepType)
            cell.update_internal_resistance()
            cell.log_state()
            return self.limits[0].targetStep

        elif self.stepType == 'Set Variable(s)':
            #            print("Running step number", self.stepIndex, "which is a step of type", self.stepType)

            zero_array = '{0:32b}'.format(int(self.zero))[::-1]
            if zero_array[0] == '1':
                cell.zero_charge_cap()
            if zero_array[1] == '1':
                cell.zero_discharge_cap()
            if zero_array[16] == '1':
                cell.set_c1(0)
            if zero_array[17] == '1':
                cell.set_c2(0)
            if zero_array[18] == '1':
                cell.set_c3(0)
            if zero_array[19] == '1':
                cell.set_c4(0)

            increment_array = '{0:32b}'.format(int(self.increment))[::-1]
            if increment_array[0] == '1':
                cell.change_cycle_index(1)
            if increment_array[1] == '1':
                cell.change_c1(1)
            if increment_array[2] == '1':
                cell.change_c2(1)
            if increment_array[3] == '1':
                cell.change_c3(1)
            if increment_array[4] == '1':
                cell.change_c4(1)

            decrement_array = '{0:32b}'.format(int(self.decrement))[::-1]
            if decrement_array[0] == '1':
                cell.change_c1(-1)
            if decrement_array[1] == '1':
                cell.change_c2(-1)
            if decrement_array[2] == '1':
                cell.change_c3(-1)
            if decrement_array[3] == '1':
                cell.change_c4(-1)

            cell.log_state()

            is_triggered, go_to = self.check_limits(cell.current_state)
            if not is_triggered:
                go_to = "Next Step"

            return go_to

    def check_limits(self, current_state):
        return_bool = False
        return_go_to = ""

        for limit in self.limits:
            is_triggered, go_to = limit.check_trigger(current_state)
            if is_triggered is True and limit.limitParameter != "PV_CHAN_Step_Time":
                return is_triggered, go_to
            elif is_triggered:
                return_bool = is_triggered
                return_go_to = go_to

        return return_bool, return_go_to

    def check_log_limits(self, current_state):
        for limit in self.log_limits:
            is_triggered, go_to = limit.check_trigger(current_state)
            if is_triggered:
                return True
        return False


class Limit:
    def __init__(self, limit_info, formulas):
        self.limitInfo = limit_info
        self.formulas = formulas
        ops = {
            '<': operator.lt,
            '<=': operator.le,
            '==': operator.eq,
            '!=': operator.ne,
            '>=': operator.ge,
            '>': operator.gt
        }

        self.limitParameter = limit_info['Equation0_szLeft']
        self.limitOperator = ops[limit_info['Equation0_szCompareSign']]

        try:
            self.limitValue = float(limit_info['Equation0_szRight'])
        except ValueError:
            self.limitValue = formulas[limit_info['Equation0_szRight']].get_value()
        self.targetStep = limit_info['m_szGotoStep']

        print('Limit parameter:', self.limitParameter)
        print('Limit operator:', self.limitOperator)
        print('Limit value:', self.limitValue)
        print('Target step:', self.targetStep)

    def update(self):
        try:
            self.limitValue = float(self.limitInfo['Equation0_szRight'])
        except ValueError:
            self.limitValue = self.formulas[self.limitInfo['Equation0_szRight']].get_value()

    def check_trigger(self, current_state):
        is_triggered = False
        go_to = self.targetStep

        if self.limitParameter in current_state.keys():
            if self.limitOperator(current_state[self.limitParameter], self.limitValue):
                is_triggered = True
                if is_triggered and self.limitParameter == "PV_CHAN_Voltage":
                    current_state[self.limitParameter] = self.limitValue

        return is_triggered, go_to


class Cell:
    def __init__(self, delta_time, cell_type, mass, specific_capacity, soc_length=20):
        self.soc_length = soc_length
        self.delta_time = delta_time

        self.log = []
        self.voltageResponse = ResponseFunction(cell_type)

        self.mass = mass
        self.specificCapacity = specific_capacity
        self.nominalCapacity = mass * specific_capacity
        self.currentCapacity = 0
        self.soc_distribution = [0 for i in range(soc_length)]
        self.lastPrint = time.time()
        self.lastLogVoltage = 0
        self.temp_soc_distribution = [0 for i in range(soc_length)]
        self.crate = None

        self.current_state = {"PV_CHAN_Voltage": 0,
                              "PV_CHAN_Current": 0,
                              "PV_CHAN_Test_Time": 0,
                              "PV_CHAN_Step_Time": 0,
                              "PV_CHAN_Cycle_Index": 1,
                              "PV_CHAN_Step_Index": 1,
                              "PV_CHAN_Charge_Capacity": 0,
                              "PV_CHAN_Discharge_Capacity": 0,
                              "TC_Counter1": 0,
                              "TC_Counter2": 0,
                              "TC_Counter3": 0,
                              "TC_Counter4": 0,
                              "Internal_Resistance": 0,
                              "Current_Capacity": 0,
                              "Surface_Capacity": 0,
                              "Capacity_Profile": 0,
                              "Formula_Values": 0,
                              "DV_Time": 0,
                              "DV_Voltage": 0,
                              "MV_Mass": self.mass,
                              "MV_SpecificCapacity": self.specificCapacity}

    def increment_time(self):
        self.current_state["PV_CHAN_Test_Time"] += self.delta_time
        self.current_state["PV_CHAN_Step_Time"] += self.delta_time
        self.current_state["DV_Time"] += self.delta_time

    def increment_current(self, crate=None, current=None, constant_voltage=None):
        if current == 'floating':
            distribution_factor = self.delta_time / 10
            self.crate = -((self.voltageResponse.pot_to_soc(constant_voltage) * self.nominalCapacity -
                            self.soc_distribution[1]) * distribution_factor) / (
                                 self.nominalCapacity * self.delta_time / 3600 * self.soc_length)
            self.soc_distribution[0] = self.voltageResponse.pot_to_soc(constant_voltage) * self.nominalCapacity
        elif current is not None:
            # print('')
            # print(current)
            # print(self.nominalCapacity)
            self.crate = current / self.nominalCapacity
            # print(self.crate)
        else:
            self.crate = crate
        self.current_state["PV_CHAN_Current"] = self.crate * self.nominalCapacity
        self.currentCapacity += -self.crate * self.nominalCapacity * self.delta_time / 3600
        self.current_state["Current_Capacity"] = self.currentCapacity
        self.update_soc_distribution(self.crate)
        self.current_state["Surface_Capacity"] = self.soc_distribution[0]

        if self.crate < 0:
            self.current_state[
                "PV_CHAN_Discharge_Capacity"] += -self.crate * self.nominalCapacity * self.delta_time / 3600
        elif self.crate > 0:
            self.current_state["PV_CHAN_Charge_Capacity"] += self.crate * self.nominalCapacity * self.delta_time / 3600

    def update_internal_resistance(self):
        self.current_state["Internal_Resistance"] = (1 - self.currentCapacity / self.nominalCapacity) \
                                                    * 10 + np.random.random() * 5

    def update_soc_distribution(self, crate):
        distribution_factor = self.delta_time / 10
        for i in range(1, self.soc_length - 1):
            self.temp_soc_distribution[i] = self.soc_distribution[i] * (1 - distribution_factor * 2) + (
                    self.soc_distribution[i - 1] + self.soc_distribution[i + 1]) * distribution_factor

        self.temp_soc_distribution[0] = self.soc_distribution[0] - crate * self.nominalCapacity * self.delta_time / \
            3600 * self.soc_length - (self.soc_distribution[0] - self.soc_distribution[1]) * distribution_factor
        self.temp_soc_distribution[-1] = self.soc_distribution[-1] + (
                self.soc_distribution[-2] - self.soc_distribution[-1]) * distribution_factor
        self.soc_distribution = self.temp_soc_distribution
        self.current_state["Capacity_Profile"] = self.soc_distribution

    def update_cell_voltage(self):
        nominal_voltage = self.voltageResponse.fast_soc_to_pot(self.soc_distribution[0] / self.nominalCapacity)

        ir_drop = self.current_state["PV_CHAN_Current"] * self.current_state["Internal_Resistance"]
        #        ir_drop = 0
        self.current_state["PV_CHAN_Voltage"] = nominal_voltage + ir_drop
        self.current_state["DV_Voltage"] = abs(self.lastLogVoltage - self.current_state["PV_CHAN_Voltage"])

    def zero_charge_cap(self):
        self.current_state["PV_CHAN_Charge_Capacity"] = 0

    def zero_discharge_cap(self):
        self.current_state["PV_CHAN_Discharge_Capacity"] = 0

    def zero_step_time(self):
        self.current_state["PV_CHAN_Step_Time"] = 0

    def set_step_index(self, stepindex):
        self.current_state["PV_CHAN_Step_Index"] = stepindex

    def set_cycle_index(self, i):
        self.current_state["PV_CHAN_Cycle_Index"] = i

    def set_c1(self, c1):
        self.current_state["TC_Counter1"] = c1

    def set_c2(self, c2):
        self.current_state["TC_Counter2"] = c2

    def set_c3(self, c3):
        self.current_state["TC_Counter3"] = c3

    def set_c4(self, c4):
        self.current_state["TC_Counter4"] = c4

    def change_cycle_index(self, ic):
        print("Cycles done:", self.current_state["PV_CHAN_Cycle_Index"])
        self.current_state["PV_CHAN_Cycle_Index"] += ic

    def change_c1(self, c1c):
        self.current_state["TC_Counter1"] += c1c

    def change_c2(self, c2c):
        self.current_state["TC_Counter2"] += c2c

    def change_c3(self, c3c):
        self.current_state["TC_Counter3"] += c3c

    def change_c4(self, c4c):
        self.current_state["TC_Counter4"] += c4c

    def log_state(self):
        self.log.append([i for i in self.current_state.values()])
        self.lastLogVoltage = self.current_state["PV_CHAN_Voltage"]
        self.current_state["DV_Time"] = 0

