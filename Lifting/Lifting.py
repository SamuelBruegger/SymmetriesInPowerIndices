class Lifting():
    def __init__(self):
        self.gobal_var_to_id_dict = {}

    def find_symmetric_variables(self, gobal_var_to_id_dict):
        symmetric_variables = {}
        for variable, id_set in gobal_var_to_id_dict.items():
            id_tuple = tuple(sorted(id_set))
            if len(id_tuple) > 1:
                if id_tuple in symmetric_variables:
                    symmetric_variables[id_tuple].append(variable)
                else:
                    symmetric_variables[id_tuple] = [variable]

        symmetric_variables = {key: value for key, value in symmetric_variables.items() if len(value) > 1}
                
        return symmetric_variables.values()

    def create_lifted_variable_dict(self, symmetric_variables):
        lifted_variable_dict = {}
        var_to_lifted_var_dict = {}
        lifted_index = 0
        for variable_tuple in symmetric_variables:
            lifted_variable_dict[lifted_index] = variable_tuple
            lifted_index += 1

        var_to_lifted_var_dict = {}
        for lifted_var, variable_tuple in lifted_variable_dict.items():
            for variable in variable_tuple:
                var_to_lifted_var_dict[variable] = lifted_var

        return lifted_variable_dict, var_to_lifted_var_dict

    def assign_id(self, formula, current_id = 0, gobal_var_to_id_dict = {}):
        formula.id = current_id
        current_id += 1

        for subformula in formula.subformula:
            if isinstance(subformula, type(formula)):
                current_id = self.assign_id(subformula, current_id, gobal_var_to_id_dict)
            else:
                if subformula not in gobal_var_to_id_dict:
                    gobal_var_to_id_dict[subformula] = {formula.id}
                else:
                    gobal_var_to_id_dict[subformula].add(formula.id)

        return current_id

    def lift_formula(self, formula, current_id = 0):
        gobal_var_to_id_dict = {}
        self.assign_id(formula, 0, gobal_var_to_id_dict)

        symmetric_variables =  self.find_symmetric_variables(gobal_var_to_id_dict)
        lifted_variable_dict, var_to_lifted_var_dict = self.create_lifted_variable_dict(symmetric_variables)
        self.lift_variables(formula, var_to_lifted_var_dict, current_id)
        return lifted_variable_dict, gobal_var_to_id_dict

    def lift_variables(self, formula, var_to_lifted_var_dict, current_id):
        for index, subformula in enumerate(formula.subformula):
            if isinstance(subformula, type(formula)):
                self.lift_variables(subformula, var_to_lifted_var_dict, current_id)
            else:
                if subformula in var_to_lifted_var_dict:
                    if str(var_to_lifted_var_dict[subformula] + current_id) in formula.subformula:
                        formula.subformula.pop(index)
                    else:
                        formula.subformula[index] = str(var_to_lifted_var_dict[subformula] + current_id)


    gobal_var_to_clause_dict = {}

    def lift_read_once_clause(self, formula, current_var=0):
        variables_dict = formula.get_variable_dict(formula.subformula)
        variables_to_lift = []
        for subformula in formula.subformula:
            if isinstance(subformula, type(formula)):
                current_var = self.lift_read_once_clause(subformula, current_var)
            else:
                if variables_dict[subformula] == 1:
                    variables_to_lift.append(subformula)
        if len(variables_to_lift) > 1:
            for variable in variables_to_lift:
                formula.subformula.remove(variable)

            formula.subformula.append(str(current_var))
            self.gobal_var_to_clause_dict[current_var] = {"operator": formula.operator, "subformula": variables_to_lift}
            current_var += 1

        formula.get_variable_dict(formula.subformula)
        return current_var