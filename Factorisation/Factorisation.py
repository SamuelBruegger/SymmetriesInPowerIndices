import pandas as pd
import sqlite3
import re
import json
import itertools
import random
import time
import os

class Factorisation():
    def __init__(self):

        self.conn = sqlite3.connect('test.db')
        self.cursor = self.conn.cursor()

    def getConnAndCursor():
        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()
        return conn, cursor
    

    def aggregate(self, setOfVariables, tableName, aggregationVariable):
        newTableName = tableName + "_a"
        setOfVariablesWithoutAggregation = setOfVariables.copy()
        setOfVariablesWithoutAggregation.remove(aggregationVariable)
        setOfVariables.remove(aggregationVariable)
        setOfVariables.append(aggregationVariable)
        #print(setOfVariables)

        if len(setOfVariablesWithoutAggregation) == 0:
            return tableName

        createQuery = f'CREATE TABLE IF NOT EXISTS {newTableName} ({", ".join(setOfVariablesWithoutAggregation)} TEXT, {aggregationVariable} TEXT)'
        #aggregateQuery = f'SELECT {aggregationVariable}, GROUP_CONCAT({", ".join(setOfVariables)}) as {aggregationVariable} FROM {tableName} GROUP BY {aggregationVariable}'
        aggregateQuery = f'INSERT INTO {newTableName} SELECT {", ".join(setOfVariablesWithoutAggregation)}, GROUP_CONCAT({aggregationVariable}) FROM {tableName} GROUP BY {", ".join(setOfVariablesWithoutAggregation)}'
        
        self.cursor.execute(createQuery)
        self.cursor.execute(aggregateQuery)
        try:
            self.cursor.execute(f"DROP TABLE {tableName}")
        except:
            pass

        self.cursor.execute(f'SELECT * FROM {newTableName}')
        #print(cursor.fetchall())
        
        self.conn.commit()
        return newTableName

    def propagate(self, setOfVariables, tableName, propagationVariable):
        newTableName = tableName + "_p"
        setOfVariablesWithoutPropagation = setOfVariables.copy()
        setOfVariablesWithoutPropagation.remove(propagationVariable[1])
        setOfVariablesWithoutPropagation.remove(propagationVariable[0])
        setOfVariablesWithoutPropagation.insert(0, propagationVariable[0])

        setOfVariables.remove(propagationVariable[1])
        setOfVariables.remove(propagationVariable[0])
        setOfVariables.insert(0, propagationVariable[0])
        #print(setOfVariables)

        createQuery = f'CREATE TABLE IF NOT EXISTS {newTableName} ({", ".join(setOfVariablesWithoutPropagation)} TEXT)'
        setOfVariablesWithoutPropagation.remove(propagationVariable[0])

        #'SELECT \'(\' || grouped_R || \') (\' || grouped_S || \')\' FROM (SELECT grouped_R, GROUP_CONCAT(S) as grouped_S FROM (SELECT S, GROUP_CONCAT(R) as grouped_R FROM dnf GROUP BY S) GROUP BY grouped_R)'
        if len(setOfVariablesWithoutPropagation) == 0:
            propagateQuery = f'INSERT INTO {newTableName} SELECT \'(\' || {propagationVariable[0]} || \')*(\' || {propagationVariable[1]} || \')\' FROM {tableName}'
        else:
            propagateQuery = f'INSERT INTO {newTableName} SELECT \'(\' || {propagationVariable[0]} || \')*(\' || {propagationVariable[1]} || \')\' as {propagationVariable[0]}, {", ".join(setOfVariablesWithoutPropagation)} TEXT FROM {tableName}'

        self.cursor.execute(createQuery)
        self.cursor.execute(propagateQuery)
        try:
            #cursor.execute(f"DROP TABLE {tableName}")
            pass
        except:
            pass

        self.cursor.execute(f'SELECT * FROM {newTableName}')
        #print(cursor.fetchall())
        
        self.conn.commit()
        return newTableName

    def setUp(self, DNF, tableName, conn, cursor, setOfVariables):

        try:
            #cursor.execute("DROP TABLE dnf")
            pass
        except:
            pass


        columns = ', '.join([f'{var} TEXT' for var in setOfVariables])
        create_table_sql = f'CREATE TABLE IF NOT EXISTS {tableName} ({columns})'

        attempt = 0
        while attempt < 3:
            try:
                cursor.execute(create_table_sql)
                break
            except Exception as e:
                print(e)
                attempt += 1
                print("Problem creating table, retrying in 1 second with attempt number " + str(attempt))
                time.sleep(1)
                
        
        placeholders = ', '.join(['?' for _ in setOfVariables])
        insert_sql = f'INSERT INTO "{tableName}" ({", ".join(setOfVariables)}) VALUES ({placeholders})'

        for clause in DNF:
            cursor.execute(insert_sql, clause)

        conn.commit()
        return tableName
    
    def resolve_inner_signature(self, inner_signature, tableName, setOfVariables):       
        current_var = ""
        NewTableName = tableName
        #print(inner_signature)

        pattern = r'([A-Z])\*'
        matches = re.findall(pattern, inner_signature)

        for match in matches:
            #print(match + " aggregate ")
            NewTableName = self.aggregate(setOfVariables, NewTableName, match)
            inner_signature = inner_signature.replace(match + "*", match)

        for part in inner_signature:
            if part:
                if current_var:
                    #print(current_var + part + " propagate ")
                    NewTableName = self.propagate(setOfVariables, NewTableName, [current_var, part])
                    inner_signature = inner_signature.replace(part, '')
                else:
                    current_var = part
        return inner_signature, NewTableName

    def process_signature(self, original_signature, tableName, setOfVariables):
        
        signature = original_signature

        while '(' in signature:
            innermost_parentheses = re.search(r'\([^()]*\)', signature)
            signature = innermost_parentheses.group(0)[1:-1]
                    
        innermost_signature, tableName = self.resolve_inner_signature(signature, tableName, setOfVariables)
        original_signature = original_signature.replace(signature, innermost_signature)

        if '(' in original_signature:
            original_signature = re.sub(r'\((\w)\)', r'\1', original_signature)
            #print(original_signature)
            original_signature, tableName = self.process_signature(original_signature, tableName, setOfVariables)
            return original_signature, tableName
        else:    
            return original_signature, tableName

    def factorisation(self, DNF, tableNameInput, setOfVariables, signature):

        #conn, cursor = getConnAndCursor()
        
        tableName = self.setUp(DNF, tableNameInput, self.conn, self.cursor, setOfVariables)

        signature, tableName =self.process_signature(signature, tableName, setOfVariables)

        self.cursor.execute(f'SELECT * FROM {tableName}')
        rows = self.cursor.fetchall()
        
        #factorised_string = re.sub(r'\((\w\w|\w\w\w)\)', r'\1', rows[0][0])
        #cursor.close()
        #conn.close()

        return rows #factorised_string
    
    def parse_subformula(self, subformula):
        # Check if subformula is a single operand
        if not any(op in subformula for op in '*,'):
            return subformula.strip()
        
        result = {'operator': None, 'subformula': []}
        
        # Determine the main operator at this level
        if '*' in subformula:
            result['operator'] = 'and'
        elif ',' in subformula:
            result['operator'] = 'or'
        
        parts = []
        balance = 0
        current_part = []
       
        for char in subformula:
            if char == '(':
                balance += 1
            elif char == ')':
                balance -= 1
            if (char == '*' and balance == 0 and result['operator'] == 'and'):
                parts.append(''.join(current_part).strip())
                current_part.clear()
            else:
                current_part.append(char)

        parts.append(''.join(current_part).strip())
        
        for part in parts:
            if part.startswith('(') and part.endswith(')'):
                result['subformula'].append(self.parse_formula(part[1:-1]))
            else:
                result['subformula'].append(part)
        
        return result
    
    def parse_formula(self, formula):
        formula = formula.strip()
               
        #if formula.startswith('(') and formula.endswith(')'):
        #    return parse_formula(formula[1:-1])

        # Split the main formula by top-level commas
        subformulas = []
        balance = 0
        last_split = 0
        for i, char in enumerate(formula):
            if char == '(':
                balance += 1
            elif char == ')':
                balance -= 1
            elif char == ',' and balance == 0:
                subformulas.append(formula[last_split:i].strip())
                last_split = i + 1
        subformulas.append(formula[last_split:].strip())
       
        if len(subformulas) == 1:
            return self.parse_subformula(subformulas[0])
        else:
            return {
                'operator': 'or',
                'subformula': [self.parse_subformula(sub) for sub in subformulas]
            }
    
    def reduceDepth(self, formula):
        parentOperator = formula["operator"]

        isFinalDepth = True

        for clause in formula["subformula"]:
            try:
                clause["operator"]
                isFinalDepth = False
                break
            except:
                continue

        if isFinalDepth:
            return formula
            
        for index, clause in enumerate(formula["subformula"]):
            try:
                if clause["operator"] == parentOperator:
                    formula["subformula"].pop(index)
                    formula["subformula"] += clause["subformula"]
                    self.reduceDepth(formula)
                else:
                    formula["subformula"][index] = self.reduceDepth(clause)  

            except:
                continue

        return formula
    
    def generate_best_Signature(self, df, listOfVariables, run):
        signatureSet = []
        permutations = list(itertools.permutations(listOfVariables))
        lenPermutations = len(permutations)
        if lenPermutations > 100:
            for i in range(5000):
                p = permutations[random.randint(0, lenPermutations-1)]
                signature = "(" + "*(".join(p[:-1]) + "*" + p[-1] + ")*"*(len(p)-1)
                if signature in signatureSet:
                        i=i-1
                else:
                    signatureSet.append(signature)
        else:
            for p in permutations:
                signature = "(" + "*(".join(p[:-1]) + "*" + p[-1] + ")*"*(len(p)-1)
                if signature not in signatureSet:
                    signatureSet.append(signature)

        factorisedSize = {}
        for index, signature in enumerate(signatureSet):
            print(signature)
            tableName = f"dnf_{run}_signature_{index}"
            
            rows = self.factorisation(df['DNF'], tableName, listOfVariables.copy(), signature)
            length_factorised = 0
            for row in rows:
                for clause in row:
                    length_factorised += len(clause)

            factorisedSize[signature] = length_factorised

        best_signature = min(factorisedSize.items(), key=lambda x: x[1])[0]
        return best_signature
    
    def create_factorsied_formula(self, DNF, listOfVariables, signature, index):
        rows = self.factorisation(DNF, f"dnf_{index}", listOfVariables, signature)
        factorised_rows = []
        for row in rows:
            factorised_rows.append(re.sub(r'\(([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\)', r'\1', row[0]))

        factorised_string = ",".join(factorised_rows)
        parsed_boolean_formula = self.parse_formula(factorised_string)
        factorised_formula = self.reduceDepth(parsed_boolean_formula)
        return factorised_formula