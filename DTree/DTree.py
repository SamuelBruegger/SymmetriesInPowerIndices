from enum import Enum
from DTree.Formula import formula

class DTREE_GATE(Enum):
    Independent_Or = 1
    Independent_And = 2
    Exclusive_Or = 3
    Empty_Gate = 4

class Dtree:
    def __init__(self, dtrees, gate: DTREE_GATE, hidden_variable=None):
        self.formula: formula = None
        self.dtree1: Dtree = None
        self.dtree2: Dtree = None
        self.hidden_variable = hidden_variable

        if gate is None or gate == DTREE_GATE.Empty_Gate:
            is_last_level = True
            try:
                for element in dtrees.subformula:
                    if not isinstance(element, str):
                        is_last_level = False
                        break
            except:
                pass

            if is_last_level:
                self.formula = dtrees
                self.size = 1
                self.gate = DTREE_GATE.Empty_Gate
            else:
                success = False
                if dtrees.operator== "or":
                    self.gate = DTREE_GATE.Independent_Or
                    success, left_formula, right_formula  = dtrees.try_to_find_independent_or()
                    #if success:
                        #print("independet or")
                elif dtrees.operator == "and" or success is False:
                    self.gate = DTREE_GATE.Independent_And
                    success, left_formula, right_formula = dtrees.try_to_find_independent_and()
                    #if success:
                        #print("independet and")
                if success is False:
                    #print("exclusive or")
                    left_formula, right_formula, removed_variable = dtrees.find_exclusive_or()
                    self.gate = DTREE_GATE.Exclusive_Or
                    if self.hidden_variable is None:
                        self.hidden_variable = []
                    if removed_variable is not None:
                        self.hidden_variable.append(removed_variable)
                #if left_formula:
                    #print("left_formula", left_formula)
                    #if not isinstance(left_formula, str) and not isinstance(left_formula, bool):
                        #print(left_formula.variables)
                #if right_formula:
                    #print("right_formula", right_formula)
                    #if not isinstance(right_formula, str) and not isinstance(right_formula, bool):
                        #print(right_formula.variables)
                self.dtree1 = Dtree(left_formula, None)
                self.dtree2 = Dtree(right_formula, None)
                self.size = self.dtree1.size + self.dtree2.size + 1 

        else:
            self.dtree1, self.dtree2 = dtrees
            self.size = self.dtree1.size + self.dtree2.size + 1
            self.gate: DTREE_GATE = gate

        self.variables = self.__get_variables__()
        self.variable_count = len(self.variables)
        self.current_satisfying_assignments = None

    def get_gate_count(self):
        if self.gate == DTREE_GATE.Empty_Gate:
            return 0
        return self.dtree1.get_gate_count() + self.dtree2.get_gate_count() + 1

    def get_length(self):
        if self.gate == DTREE_GATE.Empty_Gate:
            return 1
        return max(self.dtree1.get_length(), self.dtree2.get_length()) + 1

    def __str__(self):
        if isinstance(self.formula, str):
            return self.formula
        else:
            if self.gate == DTREE_GATE.Empty_Gate:
                return str(self.formula)
                
            return str(self.gate) + " " + str(self.dtree1) + " " + str(self.dtree2)


    def get_size(self):
        return self.size

    def __get_variables__(self):
        variables = []
        if self.formula:
            if isinstance(self.formula, str):
                variables.append(self.formula)
            elif isinstance(self.formula, bool):
                return []
            else:
                variables = list(set().union(variables, self.formula.variables))
        if self.dtree1:
            variables = list(set().union(variables, self.dtree1.variables))
        if self.dtree2:
            variables = list(set().union(variables, self.dtree2.variables))
        if self.hidden_variable is not None:
            variables = list(set().union(variables, self.hidden_variable))
        return variables 
                   
    def satisfying_assignments(self, var_to_lifted_var = {}, lifting_dict = {}):
        if self.current_satisfying_assignments is not None:
            return self.current_satisfying_assignments

        if self.gate is None or self.gate == DTREE_GATE.Empty_Gate:
            if isinstance(self.formula, str) or isinstance(self.formula, int):
                if self.formula in lifting_dict:
                    if lifting_dict[self.formula]["operator"] == "or":
                        return 2 ** len(lifting_dict[self.formula]["subformula"]) - 1
                    if lifting_dict[self.formula]["operator"] == "and":
                        return 1
                else:
                    return 1
            if isinstance(self.formula, bool):
                if self.formula:
                    return 1
                else:
                    return 0
            else:
                self.current_satisfying_assignments = self.formula.satisfying_assignments()
            return self.current_satisfying_assignments

        dtree1_assignments = self.dtree1.satisfying_assignments(var_to_lifted_var, lifting_dict)
        dtree2_assignments = self.dtree2.satisfying_assignments(var_to_lifted_var, lifting_dict)

        if self.gate == DTREE_GATE.Independent_Or:
            list_var_dtree1 = []
            for var in self.dtree1.variables:
                if var in lifting_dict and type(lifting_dict[var]["subformula"]) is list:
                    list_var_dtree1.extend(lifting_dict[var]["subformula"])
                else:
                    list_var_dtree1.append(var)
            dtree1_variable_count = len(set(list_var_dtree1))

            list_var_dtree2 = []
            for var in self.dtree2.variables:
                if var in lifting_dict and type(lifting_dict[var]["subformula"]) is list:
                    list_var_dtree2.extend(lifting_dict[var]["subformula"])
                else:
                    list_var_dtree2.append(var)
            dtree2_variable_count = len(set(list_var_dtree2))


            return dtree1_assignments * (2 ** dtree2_variable_count) + \
                    dtree2_assignments * (2 ** dtree1_variable_count) - \
                    dtree1_assignments * dtree2_assignments
            

        elif self.gate == DTREE_GATE.Independent_And:
            return dtree1_assignments * dtree2_assignments
            
        elif self.gate == DTREE_GATE.Exclusive_Or:
            list_var_dtree1 = []
            for var in self.dtree1.variables:
                if var in lifting_dict and type(lifting_dict[var]["subformula"]) is list:
                    list_var_dtree1.extend(lifting_dict[var]["subformula"])
                else:
                    list_var_dtree1.append(var)

            list_var_dtree2 = []
            for var in self.dtree2.variables:
                if var in lifting_dict and type(lifting_dict[var]["subformula"]) is list:
                    list_var_dtree2.extend(lifting_dict[var]["subformula"])
                else:
                    list_var_dtree2.append(var)
            
            unique_variables1 = len([x for x in list_var_dtree1 if x not in list_var_dtree2])
            unique_variables2 = len([x for x in list_var_dtree2 if x not in list_var_dtree1])

            return dtree1_assignments * (2 ** unique_variables2) + dtree2_assignments * (2 ** unique_variables1)

        else:
            print("Error - false gate")
            raise ValueError("Error - false gate")
            return -1

    def critical_assignments_fact(self, fact, var_to_lifted_var = {}, lifting_dict = {}):
        list_of_original_variables = []
        for var in self.variables:
            if var in lifting_dict and type(lifting_dict[var]["subformula"]) is list:
                list_of_original_variables.extend(lifting_dict[var]["subformula"])
            else:
                list_of_original_variables.append(var)

        if fact not in list_of_original_variables:
            return 0

        if self.gate is None or self.gate == DTREE_GATE.Empty_Gate:
            if isinstance(self.formula, str):
                if self.formula == fact:
                    return 1
                if fact in lifting_dict[self.formula]["subformula"]:
                    if lifting_dict[self.formula]["operator"] == "or":
                        return 2 ** len(lifting_dict[self.formula]["subformula"]) - 1
                    if lifting_dict[self.formula]["operator"] == "and":
                        return 1
                return 0
            return self.formula.critical_assignments_for_fact(fact)

        if self.gate == DTREE_GATE.Independent_Or:
            list_var_dtree1 = []
            for var in self.dtree1.variables:
                if var in lifting_dict and type(lifting_dict[var]["subformula"]) is list:
                    list_var_dtree1.extend(lifting_dict[var]["subformula"])
                else:
                    list_var_dtree1.append(var)

            if fact in self.dtree1.variables or fact in list_var_dtree1:
                list_var_dtree2 = []
                for var in self.dtree2.variables:
                    if var in lifting_dict and type(lifting_dict[var]["subformula"]) is list:
                        list_var_dtree2.extend(lifting_dict[var]["subformula"])
                    else:
                        list_var_dtree2.append(var)
                dtree2_variable_count = len(set(list_var_dtree2))
                return self.dtree1.critical_assignments_fact(fact, var_to_lifted_var, lifting_dict) * (
                        (2 ** dtree2_variable_count) - self.dtree2.satisfying_assignments(var_to_lifted_var, lifting_dict))
            else:

                dtree1_variable_count = len(set(list_var_dtree1))
                return self.dtree2.critical_assignments_fact(fact, var_to_lifted_var, lifting_dict) * (
                        (2 ** dtree1_variable_count) - self.dtree1.satisfying_assignments(var_to_lifted_var, lifting_dict))

        elif self.gate == DTREE_GATE.Independent_And:
            if fact in self.dtree1.variables:
                return self.dtree1.critical_assignments_fact(fact, var_to_lifted_var, lifting_dict) * self.dtree2.satisfying_assignments(var_to_lifted_var, lifting_dict)
            else:
                return self.dtree2.critical_assignments_fact(fact, var_to_lifted_var, lifting_dict) * self.dtree1.satisfying_assignments(var_to_lifted_var, lifting_dict)

        elif self.gate == DTREE_GATE.Exclusive_Or:
            list_var_dtree1 = []
            for var in self.dtree1.variables:
                if var in lifting_dict and type(lifting_dict[var]["subformula"]) is list:
                    list_var_dtree1.extend(lifting_dict[var]["subformula"])
                else:
                    list_var_dtree1.append(var)

            list_var_dtree2 = []
            for var in self.dtree2.variables:
                if var in lifting_dict and type(lifting_dict[var]["subformula"]) is list:
                    list_var_dtree2.extend(lifting_dict[var]["subformula"])
                else:
                    list_var_dtree2.append(var)
            
            unique_variables1 = len([x for x in list_var_dtree1 if x not in list_var_dtree2])
            unique_variables2 = len([x for x in list_var_dtree2 if x not in list_var_dtree1])

            if self.hidden_variable == fact or fact in self.hidden_variable:
                return self.dtree2.satisfying_assignments(var_to_lifted_var, lifting_dict) * (
                        2 ** unique_variables1) - self.dtree1.satisfying_assignments(var_to_lifted_var, lifting_dict) * (2 ** unique_variables2)
            else:
                return self.dtree1.critical_assignments_fact(fact) * (
                        2 ** unique_variables2) + self.dtree2.critical_assignments_fact(fact) * (
                            2 ** unique_variables1)

        else:
            print("Error - false gate")
            raise ValueError("Error - false gate")
            return -1