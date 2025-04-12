# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from .utils import tree_to_variable_index


def DFG_python(root_node, index_to_code, states):
    assignment = ["assignment", "augmented_assignment", "for_in_clause"]
    if_statement = ["if_statement"]
    for_statement = ["for_statement"]
    while_statement = ["while_statement"]
    do_first_statement = ["for_in_clause"]
    def_statement = ["default_parameter"]
    states = states.copy()
    if (
            len(root_node.children) == 0 or root_node.type in ["string_literal", "string", "character_literal"]
    ) and root_node.type != "comment":
        idx, code = index_to_code[(root_node.start_point, root_node.end_point)]
        if root_node.type == code:
            return [], states
        elif code in states:
            return [(code, idx, "comesFrom", [code], states[code].copy())], states
        else:
            if root_node.type == "identifier":
                states[code] = [idx]
            return [(code, idx, "comesFrom", [], [])], states
    elif root_node.type in def_statement:
        name = root_node.child_by_field_name("name")
        value = root_node.child_by_field_name("value")
        DFG = []
        if value is None:
            indexs = tree_to_variable_index(name, index_to_code)
            for index in indexs:
                idx, code = index_to_code[index]
                DFG.append((code, idx, "comesFrom", [], []))
                states[code] = [idx]
            return sorted(DFG, key=lambda x: x[1]), states
        else:
            name_indexs = tree_to_variable_index(name, index_to_code)
            value_indexs = tree_to_variable_index(value, index_to_code)
            temp, states = DFG_python(value, index_to_code, states)
            DFG += temp
            for index1 in name_indexs:
                idx1, code1 = index_to_code[index1]
                for index2 in value_indexs:
                    idx2, code2 = index_to_code[index2]
                    DFG.append((code1, idx1, "comesFrom", [code2], [idx2]))
                states[code1] = [idx1]
            return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in assignment:
        if root_node.type == "for_in_clause":
            right_nodes = [root_node.children[-1]]
            left_nodes = [root_node.child_by_field_name("left")]
        else:
            if root_node.child_by_field_name("right") is None:
                return [], states
            left_nodes = [x for x in root_node.child_by_field_name("left").children if x.type != ","]
            right_nodes = [x for x in root_node.child_by_field_name("right").children if x.type != ","]
            if len(right_nodes) != len(left_nodes):
                left_nodes = [root_node.child_by_field_name("left")]
                right_nodes = [root_node.child_by_field_name("right")]
            if len(left_nodes) == 0:
                left_nodes = [root_node.child_by_field_name("left")]
            if len(right_nodes) == 0:
                right_nodes = [root_node.child_by_field_name("right")]
        DFG = []
        for node in right_nodes:
            temp, states = DFG_python(node, index_to_code, states)
            DFG += temp

        for left_node, right_node in zip(left_nodes, right_nodes):
            left_tokens_index = tree_to_variable_index(left_node, index_to_code)
            right_tokens_index = tree_to_variable_index(right_node, index_to_code)
            temp = []
            for token1_index in left_tokens_index:
                idx1, code1 = index_to_code[token1_index]
                temp.append(
                    (
                        code1,
                        idx1,
                        "computedFrom",
                        [index_to_code[x][1] for x in right_tokens_index],
                        [index_to_code[x][0] for x in right_tokens_index],
                    )
                )
                states[code1] = [idx1]
            DFG += temp
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in if_statement:
        DFG = []
        current_states = states.copy()
        others_states = []
        tag = False
        if "else" in root_node.type:
            tag = True
        for child in root_node.children:
            if "else" in child.type:
                tag = True
            if child.type not in ["elif_clause", "else_clause"]:
                temp, current_states = DFG_python(child, index_to_code, current_states)
                DFG += temp
            else:
                temp, new_states = DFG_python(child, index_to_code, states)
                DFG += temp
                others_states.append(new_states)
        others_states.append(current_states)
        if tag is False:
            others_states.append(states)
        new_states = {}
        for dic in others_states:
            for key in dic:
                if key not in new_states:
                    new_states[key] = dic[key].copy()
                else:
                    new_states[key] += dic[key]
        for key in new_states:
            new_states[key] = sorted(list(set(new_states[key])))
        return sorted(DFG, key=lambda x: x[1]), new_states
    elif root_node.type in for_statement:
        DFG = []
        for i in range(2):
            right_nodes = [x for x in root_node.child_by_field_name("right").children if x.type != ","]
            left_nodes = [x for x in root_node.child_by_field_name("left").children if x.type != ","]
            if len(right_nodes) != len(left_nodes):
                left_nodes = [root_node.child_by_field_name("left")]
                right_nodes = [root_node.child_by_field_name("right")]
            if len(left_nodes) == 0:
                left_nodes = [root_node.child_by_field_name("left")]
            if len(right_nodes) == 0:
                right_nodes = [root_node.child_by_field_name("right")]
            for node in right_nodes:
                temp, states = DFG_python(node, index_to_code, states)
                DFG += temp
            for left_node, right_node in zip(left_nodes, right_nodes):
                left_tokens_index = tree_to_variable_index(left_node, index_to_code)
                right_tokens_index = tree_to_variable_index(right_node, index_to_code)
                temp = []
                for token1_index in left_tokens_index:
                    idx1, code1 = index_to_code[token1_index]
                    temp.append(
                        (
                            code1,
                            idx1,
                            "computedFrom",
                            [index_to_code[x][1] for x in right_tokens_index],
                            [index_to_code[x][0] for x in right_tokens_index],
                        )
                    )
                    states[code1] = [idx1]
                DFG += temp
            if root_node.children[-1].type == "block":
                temp, states = DFG_python(root_node.children[-1], index_to_code, states)
                DFG += temp
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in while_statement:
        DFG = []
        for i in range(2):
            for child in root_node.children:
                temp, states = DFG_python(child, index_to_code, states)
                DFG += temp
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    else:
        DFG = []
        for child in root_node.children:
            if child.type in do_first_statement:
                temp, states = DFG_python(child, index_to_code, states)
                DFG += temp
        for child in root_node.children:
            if child.type not in do_first_statement:
                temp, states = DFG_python(child, index_to_code, states)
                DFG += temp

        return sorted(DFG, key=lambda x: x[1]), states


def DFG_java(root_node, index_to_code, states):
    assignment = ["assignment_expression"]
    def_statement = ["variable_declarator"]
    increment_statement = ["update_expression"]
    if_statement = ["if_statement", "else"]
    for_statement = ["for_statement"]
    enhanced_for_statement = ["enhanced_for_statement"]
    while_statement = ["while_statement"]
    do_first_statement = []
    states = states.copy()
    if (
            len(root_node.children) == 0 or root_node.type in ["string_literal", "string", "character_literal"]
    ) and root_node.type != "comment":
        idx, code = index_to_code[(root_node.start_point, root_node.end_point)]
        if root_node.type == code:
            return [], states
        elif code in states:
            return [(code, idx, "comesFrom", [code], states[code].copy())], states
        else:
            if root_node.type == "identifier":
                states[code] = [idx]
            return [(code, idx, "comesFrom", [], [])], states
    elif root_node.type in def_statement:
        name = root_node.child_by_field_name("name")
        value = root_node.child_by_field_name("value")
        DFG = []
        if value is None:
            indexs = tree_to_variable_index(name, index_to_code)
            for index in indexs:
                idx, code = index_to_code[index]
                DFG.append((code, idx, "comesFrom", [], []))
                states[code] = [idx]
            return sorted(DFG, key=lambda x: x[1]), states
        else:
            name_indexs = tree_to_variable_index(name, index_to_code)
            value_indexs = tree_to_variable_index(value, index_to_code)
            temp, states = DFG_java(value, index_to_code, states)
            DFG += temp
            for index1 in name_indexs:
                idx1, code1 = index_to_code[index1]
                for index2 in value_indexs:
                    idx2, code2 = index_to_code[index2]
                    DFG.append((code1, idx1, "comesFrom", [code2], [idx2]))
                states[code1] = [idx1]
            return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in assignment:
        left_nodes = root_node.child_by_field_name("left")
        right_nodes = root_node.child_by_field_name("right")
        DFG = []
        temp, states = DFG_java(right_nodes, index_to_code, states)
        DFG += temp
        name_indexs = tree_to_variable_index(left_nodes, index_to_code)
        value_indexs = tree_to_variable_index(right_nodes, index_to_code)
        for index1 in name_indexs:
            idx1, code1 = index_to_code[index1]
            for index2 in value_indexs:
                idx2, code2 = index_to_code[index2]
                DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
            states[code1] = [idx1]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in increment_statement:
        DFG = []
        indexs = tree_to_variable_index(root_node, index_to_code)
        for index1 in indexs:
            idx1, code1 = index_to_code[index1]
            for index2 in indexs:
                idx2, code2 = index_to_code[index2]
                DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
            states[code1] = [idx1]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in if_statement:
        DFG = []
        current_states = states.copy()
        others_states = []
        flag = False
        tag = False
        if "else" in root_node.type:
            tag = True
        for child in root_node.children:
            if "else" in child.type:
                tag = True
            if child.type not in if_statement and flag is False:
                temp, current_states = DFG_java(child, index_to_code, current_states)
                DFG += temp
            else:
                flag = True
                temp, new_states = DFG_java(child, index_to_code, states)
                DFG += temp
                others_states.append(new_states)
        others_states.append(current_states)
        if tag is False:
            others_states.append(states)
        new_states = {}
        for dic in others_states:
            for key in dic:
                if key not in new_states:
                    new_states[key] = dic[key].copy()
                else:
                    new_states[key] += dic[key]
        for key in new_states:
            new_states[key] = sorted(list(set(new_states[key])))
        return sorted(DFG, key=lambda x: x[1]), new_states
    elif root_node.type in for_statement:
        DFG = []
        for child in root_node.children:
            temp, states = DFG_java(child, index_to_code, states)
            DFG += temp
        flag = False
        for child in root_node.children:
            if flag:
                temp, states = DFG_java(child, index_to_code, states)
                DFG += temp
            elif child.type == "local_variable_declaration":
                flag = True
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in enhanced_for_statement:
        name = root_node.child_by_field_name("name")
        value = root_node.child_by_field_name("value")
        body = root_node.child_by_field_name("body")
        DFG = []
        for i in range(2):
            temp, states = DFG_java(value, index_to_code, states)
            DFG += temp
            name_indexs = tree_to_variable_index(name, index_to_code)
            value_indexs = tree_to_variable_index(value, index_to_code)
            for index1 in name_indexs:
                idx1, code1 = index_to_code[index1]
                for index2 in value_indexs:
                    idx2, code2 = index_to_code[index2]
                    DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
                states[code1] = [idx1]
            temp, states = DFG_java(body, index_to_code, states)
            DFG += temp
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in while_statement:
        DFG = []
        for i in range(2):
            for child in root_node.children:
                temp, states = DFG_java(child, index_to_code, states)
                DFG += temp
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    else:
        DFG = []
        for child in root_node.children:
            if child.type in do_first_statement:
                temp, states = DFG_java(child, index_to_code, states)
                DFG += temp
        for child in root_node.children:
            if child.type not in do_first_statement:
                temp, states = DFG_java(child, index_to_code, states)
                DFG += temp

        return sorted(DFG, key=lambda x: x[1]), states


def DFG_csharp(root_node, index_to_code, states):
    assignment = ["assignment_expression"]
    def_statement = ["variable_declarator"]
    increment_statement = ["postfix_unary_expression"]
    if_statement = ["if_statement", "else"]
    for_statement = ["for_statement"]
    enhanced_for_statement = ["for_each_statement"]
    while_statement = ["while_statement"]
    do_first_statement = []
    states = states.copy()
    if (
            len(root_node.children) == 0 or root_node.type in ["string_literal", "string", "character_literal"]
    ) and root_node.type != "comment":
        idx, code = index_to_code[(root_node.start_point, root_node.end_point)]
        if root_node.type == code:
            return [], states
        elif code in states:
            return [(code, idx, "comesFrom", [code], states[code].copy())], states
        else:
            if root_node.type == "identifier":
                states[code] = [idx]
            return [(code, idx, "comesFrom", [], [])], states
    elif root_node.type in def_statement:
        if len(root_node.children) == 2:
            name = root_node.children[0]
            value = root_node.children[1]
        else:
            name = root_node.children[0]
            value = None
        DFG = []
        if value is None:
            indexs = tree_to_variable_index(name, index_to_code)
            for index in indexs:
                idx, code = index_to_code[index]
                DFG.append((code, idx, "comesFrom", [], []))
                states[code] = [idx]
            return sorted(DFG, key=lambda x: x[1]), states
        else:
            name_indexs = tree_to_variable_index(name, index_to_code)
            value_indexs = tree_to_variable_index(value, index_to_code)
            temp, states = DFG_csharp(value, index_to_code, states)
            DFG += temp
            for index1 in name_indexs:
                idx1, code1 = index_to_code[index1]
                for index2 in value_indexs:
                    idx2, code2 = index_to_code[index2]
                    DFG.append((code1, idx1, "comesFrom", [code2], [idx2]))
                states[code1] = [idx1]
            return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in assignment:
        left_nodes = root_node.child_by_field_name("left")
        right_nodes = root_node.child_by_field_name("right")
        DFG = []
        temp, states = DFG_csharp(right_nodes, index_to_code, states)
        DFG += temp
        name_indexs = tree_to_variable_index(left_nodes, index_to_code)
        value_indexs = tree_to_variable_index(right_nodes, index_to_code)
        for index1 in name_indexs:
            idx1, code1 = index_to_code[index1]
            for index2 in value_indexs:
                idx2, code2 = index_to_code[index2]
                DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
            states[code1] = [idx1]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in increment_statement:
        DFG = []
        indexs = tree_to_variable_index(root_node, index_to_code)
        for index1 in indexs:
            idx1, code1 = index_to_code[index1]
            for index2 in indexs:
                idx2, code2 = index_to_code[index2]
                DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
            states[code1] = [idx1]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in if_statement:
        DFG = []
        current_states = states.copy()
        others_states = []
        flag = False
        tag = False
        if "else" in root_node.type:
            tag = True
        for child in root_node.children:
            if "else" in child.type:
                tag = True
            if child.type not in if_statement and flag is False:
                temp, current_states = DFG_csharp(child, index_to_code, current_states)
                DFG += temp
            else:
                flag = True
                temp, new_states = DFG_csharp(child, index_to_code, states)
                DFG += temp
                others_states.append(new_states)
        others_states.append(current_states)
        if tag is False:
            others_states.append(states)
        new_states = {}
        for dic in others_states:
            for key in dic:
                if key not in new_states:
                    new_states[key] = dic[key].copy()
                else:
                    new_states[key] += dic[key]
        for key in new_states:
            new_states[key] = sorted(list(set(new_states[key])))
        return sorted(DFG, key=lambda x: x[1]), new_states
    elif root_node.type in for_statement:
        DFG = []
        for child in root_node.children:
            temp, states = DFG_csharp(child, index_to_code, states)
            DFG += temp
        flag = False
        for child in root_node.children:
            if flag:
                temp, states = DFG_csharp(child, index_to_code, states)
                DFG += temp
            elif child.type == "local_variable_declaration":
                flag = True
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in enhanced_for_statement:
        name = root_node.child_by_field_name("left")
        value = root_node.child_by_field_name("right")
        body = root_node.child_by_field_name("body")
        DFG = []
        for i in range(2):
            temp, states = DFG_csharp(value, index_to_code, states)
            DFG += temp
            name_indexs = tree_to_variable_index(name, index_to_code)
            value_indexs = tree_to_variable_index(value, index_to_code)
            for index1 in name_indexs:
                idx1, code1 = index_to_code[index1]
                for index2 in value_indexs:
                    idx2, code2 = index_to_code[index2]
                    DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
                states[code1] = [idx1]
            temp, states = DFG_csharp(body, index_to_code, states)
            DFG += temp
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in while_statement:
        DFG = []
        for i in range(2):
            for child in root_node.children:
                temp, states = DFG_csharp(child, index_to_code, states)
                DFG += temp
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    else:
        DFG = []
        for child in root_node.children:
            if child.type in do_first_statement:
                temp, states = DFG_csharp(child, index_to_code, states)
                DFG += temp
        for child in root_node.children:
            if child.type not in do_first_statement:
                temp, states = DFG_csharp(child, index_to_code, states)
                DFG += temp

        return sorted(DFG, key=lambda x: x[1]), states


def DFG_ruby(root_node, index_to_code, states):
    assignment = ["assignment", "operator_assignment"]
    if_statement = ["if", "elsif", "else", "unless", "when"]
    for_statement = ["for"]
    while_statement = ["while_modifier", "until"]
    do_first_statement = []
    def_statement = ["keyword_parameter"]
    if (
            len(root_node.children) == 0 or root_node.type in ["string_literal", "string", "character_literal"]
    ) and root_node.type != "comment":
        states = states.copy()
        idx, code = index_to_code[(root_node.start_point, root_node.end_point)]
        if root_node.type == code:
            return [], states
        elif code in states:
            return [(code, idx, "comesFrom", [code], states[code].copy())], states
        else:
            if root_node.type == "identifier":
                states[code] = [idx]
            return [(code, idx, "comesFrom", [], [])], states
    elif root_node.type in def_statement:
        name = root_node.child_by_field_name("name")
        value = root_node.child_by_field_name("value")
        DFG = []
        if value is None:
            indexs = tree_to_variable_index(name, index_to_code)
            for index in indexs:
                idx, code = index_to_code[index]
                DFG.append((code, idx, "comesFrom", [], []))
                states[code] = [idx]
            return sorted(DFG, key=lambda x: x[1]), states
        else:
            name_indexs = tree_to_variable_index(name, index_to_code)
            value_indexs = tree_to_variable_index(value, index_to_code)
            temp, states = DFG_ruby(value, index_to_code, states)
            DFG += temp
            for index1 in name_indexs:
                idx1, code1 = index_to_code[index1]
                for index2 in value_indexs:
                    idx2, code2 = index_to_code[index2]
                    DFG.append((code1, idx1, "comesFrom", [code2], [idx2]))
                states[code1] = [idx1]
            return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in assignment:
        left_nodes = [x for x in root_node.child_by_field_name("left").children if x.type != ","]
        right_nodes = [x for x in root_node.child_by_field_name("right").children if x.type != ","]
        if len(right_nodes) != len(left_nodes):
            left_nodes = [root_node.child_by_field_name("left")]
            right_nodes = [root_node.child_by_field_name("right")]
        if len(left_nodes) == 0:
            left_nodes = [root_node.child_by_field_name("left")]
        if len(right_nodes) == 0:
            right_nodes = [root_node.child_by_field_name("right")]
        if root_node.type == "operator_assignment":
            left_nodes = [root_node.children[0]]
            right_nodes = [root_node.children[-1]]

        DFG = []
        for node in right_nodes:
            temp, states = DFG_ruby(node, index_to_code, states)
            DFG += temp

        for left_node, right_node in zip(left_nodes, right_nodes):
            left_tokens_index = tree_to_variable_index(left_node, index_to_code)
            right_tokens_index = tree_to_variable_index(right_node, index_to_code)
            temp = []
            for token1_index in left_tokens_index:
                idx1, code1 = index_to_code[token1_index]
                temp.append(
                    (
                        code1,
                        idx1,
                        "computedFrom",
                        [index_to_code[x][1] for x in right_tokens_index],
                        [index_to_code[x][0] for x in right_tokens_index],
                    )
                )
                states[code1] = [idx1]
            DFG += temp
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in if_statement:
        DFG = []
        current_states = states.copy()
        others_states = []
        tag = False
        if "else" in root_node.type:
            tag = True
        for child in root_node.children:
            if "else" in child.type:
                tag = True
            if child.type not in if_statement:
                temp, current_states = DFG_ruby(child, index_to_code, current_states)
                DFG += temp
            else:
                temp, new_states = DFG_ruby(child, index_to_code, states)
                DFG += temp
                others_states.append(new_states)
        others_states.append(current_states)
        if tag is False:
            others_states.append(states)
        new_states = {}
        for dic in others_states:
            for key in dic:
                if key not in new_states:
                    new_states[key] = dic[key].copy()
                else:
                    new_states[key] += dic[key]
        for key in new_states:
            new_states[key] = sorted(list(set(new_states[key])))
        return sorted(DFG, key=lambda x: x[1]), new_states
    elif root_node.type in for_statement:
        DFG = []
        for i in range(2):
            left_nodes = [root_node.child_by_field_name("pattern")]
            right_nodes = [root_node.child_by_field_name("value")]
            assert len(right_nodes) == len(left_nodes)
            for node in right_nodes:
                temp, states = DFG_ruby(node, index_to_code, states)
                DFG += temp
            for left_node, right_node in zip(left_nodes, right_nodes):
                left_tokens_index = tree_to_variable_index(left_node, index_to_code)
                right_tokens_index = tree_to_variable_index(right_node, index_to_code)
                temp = []
                for token1_index in left_tokens_index:
                    idx1, code1 = index_to_code[token1_index]
                    temp.append(
                        (
                            code1,
                            idx1,
                            "computedFrom",
                            [index_to_code[x][1] for x in right_tokens_index],
                            [index_to_code[x][0] for x in right_tokens_index],
                        )
                    )
                    states[code1] = [idx1]
                DFG += temp
            temp, states = DFG_ruby(root_node.child_by_field_name("body"), index_to_code, states)
            DFG += temp
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in while_statement:
        DFG = []
        for i in range(2):
            for child in root_node.children:
                temp, states = DFG_ruby(child, index_to_code, states)
                DFG += temp
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    else:
        DFG = []
        for child in root_node.children:
            if child.type in do_first_statement:
                temp, states = DFG_ruby(child, index_to_code, states)
                DFG += temp
        for child in root_node.children:
            if child.type not in do_first_statement:
                temp, states = DFG_ruby(child, index_to_code, states)
                DFG += temp

        return sorted(DFG, key=lambda x: x[1]), states


def DFG_go(root_node, index_to_code, states):
    assignment = [
        "assignment_statement",
    ]
    def_statement = ["var_spec"]
    increment_statement = ["inc_statement"]
    if_statement = ["if_statement", "else"]
    for_statement = ["for_statement"]
    do_first_statement = []
    states = states.copy()
    if (
            len(root_node.children) == 0 or root_node.type in ["string_literal", "string", "character_literal"]
    ) and root_node.type != "comment":
        idx, code = index_to_code[(root_node.start_point, root_node.end_point)]
        if root_node.type == code:
            return [], states
        elif code in states:
            return [(code, idx, "comesFrom", [code], states[code].copy())], states
        else:
            if root_node.type == "identifier":
                states[code] = [idx]
            return [(code, idx, "comesFrom", [], [])], states
    elif root_node.type in def_statement:
        name = root_node.child_by_field_name("name")
        value = root_node.child_by_field_name("value")
        DFG = []
        if value is None:
            indexs = tree_to_variable_index(name, index_to_code)
            for index in indexs:
                idx, code = index_to_code[index]
                DFG.append((code, idx, "comesFrom", [], []))
                states[code] = [idx]
            return sorted(DFG, key=lambda x: x[1]), states
        else:
            name_indexs = tree_to_variable_index(name, index_to_code)
            value_indexs = tree_to_variable_index(value, index_to_code)
            temp, states = DFG_go(value, index_to_code, states)
            DFG += temp
            for index1 in name_indexs:
                idx1, code1 = index_to_code[index1]
                for index2 in value_indexs:
                    idx2, code2 = index_to_code[index2]
                    DFG.append((code1, idx1, "comesFrom", [code2], [idx2]))
                states[code1] = [idx1]
            return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in assignment:
        left_nodes = root_node.child_by_field_name("left")
        right_nodes = root_node.child_by_field_name("right")
        DFG = []
        temp, states = DFG_go(right_nodes, index_to_code, states)
        DFG += temp
        name_indexs = tree_to_variable_index(left_nodes, index_to_code)
        value_indexs = tree_to_variable_index(right_nodes, index_to_code)
        for index1 in name_indexs:
            idx1, code1 = index_to_code[index1]
            for index2 in value_indexs:
                idx2, code2 = index_to_code[index2]
                DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
            states[code1] = [idx1]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in increment_statement:
        DFG = []
        indexs = tree_to_variable_index(root_node, index_to_code)
        for index1 in indexs:
            idx1, code1 = index_to_code[index1]
            for index2 in indexs:
                idx2, code2 = index_to_code[index2]
                DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
            states[code1] = [idx1]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in if_statement:
        DFG = []
        current_states = states.copy()
        others_states = []
        flag = False
        tag = False
        if "else" in root_node.type:
            tag = True
        for child in root_node.children:
            if "else" in child.type:
                tag = True
            if child.type not in if_statement and flag is False:
                temp, current_states = DFG_go(child, index_to_code, current_states)
                DFG += temp
            else:
                flag = True
                temp, new_states = DFG_go(child, index_to_code, states)
                DFG += temp
                others_states.append(new_states)
        others_states.append(current_states)
        if tag is False:
            others_states.append(states)
        new_states = {}
        for dic in others_states:
            for key in dic:
                if key not in new_states:
                    new_states[key] = dic[key].copy()
                else:
                    new_states[key] += dic[key]
        for key in states:
            if key not in new_states:
                new_states[key] = states[key]
            else:
                new_states[key] += states[key]
        for key in new_states:
            new_states[key] = sorted(list(set(new_states[key])))
        return sorted(DFG, key=lambda x: x[1]), new_states
    elif root_node.type in for_statement:
        DFG = []
        for child in root_node.children:
            temp, states = DFG_go(child, index_to_code, states)
            DFG += temp
        flag = False
        for child in root_node.children:
            if flag:
                temp, states = DFG_go(child, index_to_code, states)
                DFG += temp
            elif child.type == "for_clause":
                if child.child_by_field_name("update") is not None:
                    temp, states = DFG_go(child.child_by_field_name("update"), index_to_code, states)
                    DFG += temp
                flag = True
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    else:
        DFG = []
        for child in root_node.children:
            if child.type in do_first_statement:
                temp, states = DFG_go(child, index_to_code, states)
                DFG += temp
        for child in root_node.children:
            if child.type not in do_first_statement:
                temp, states = DFG_go(child, index_to_code, states)
                DFG += temp

        return sorted(DFG, key=lambda x: x[1]), states


def DFG_php(root_node, index_to_code, states):
    assignment = ["assignment_expression", "augmented_assignment_expression"]
    def_statement = ["simple_parameter"]
    increment_statement = ["update_expression"]
    if_statement = ["if_statement", "else_clause"]
    for_statement = ["for_statement"]
    enhanced_for_statement = ["foreach_statement"]
    while_statement = ["while_statement"]
    do_first_statement = []
    states = states.copy()
    if (
            len(root_node.children) == 0 or root_node.type in ["string_literal", "string", "character_literal"]
    ) and root_node.type != "comment":
        idx, code = index_to_code[(root_node.start_point, root_node.end_point)]
        if root_node.type == code:
            return [], states
        elif code in states:
            return [(code, idx, "comesFrom", [code], states[code].copy())], states
        else:
            if root_node.type == "identifier":
                states[code] = [idx]
            return [(code, idx, "comesFrom", [], [])], states
    elif root_node.type in def_statement:
        name = root_node.child_by_field_name("name")
        value = root_node.child_by_field_name("default_value")
        DFG = []
        if value is None:
            indexs = tree_to_variable_index(name, index_to_code)
            for index in indexs:
                idx, code = index_to_code[index]
                DFG.append((code, idx, "comesFrom", [], []))
                states[code] = [idx]
            return sorted(DFG, key=lambda x: x[1]), states
        else:
            name_indexs = tree_to_variable_index(name, index_to_code)
            value_indexs = tree_to_variable_index(value, index_to_code)
            temp, states = DFG_php(value, index_to_code, states)
            DFG += temp
            for index1 in name_indexs:
                idx1, code1 = index_to_code[index1]
                for index2 in value_indexs:
                    idx2, code2 = index_to_code[index2]
                    DFG.append((code1, idx1, "comesFrom", [code2], [idx2]))
                states[code1] = [idx1]
            return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in assignment:
        left_nodes = root_node.child_by_field_name("left")
        right_nodes = root_node.child_by_field_name("right")
        DFG = []
        temp, states = DFG_php(right_nodes, index_to_code, states)
        DFG += temp
        name_indexs = tree_to_variable_index(left_nodes, index_to_code)
        value_indexs = tree_to_variable_index(right_nodes, index_to_code)
        for index1 in name_indexs:
            idx1, code1 = index_to_code[index1]
            for index2 in value_indexs:
                idx2, code2 = index_to_code[index2]
                DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
            states[code1] = [idx1]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in increment_statement:
        DFG = []
        indexs = tree_to_variable_index(root_node, index_to_code)
        for index1 in indexs:
            idx1, code1 = index_to_code[index1]
            for index2 in indexs:
                idx2, code2 = index_to_code[index2]
                DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
            states[code1] = [idx1]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in if_statement:
        DFG = []
        current_states = states.copy()
        others_states = []
        flag = False
        if "else" in root_node.type:
            pass
        for child in root_node.children:
            if "else" in child.type:
                pass
            if child.type not in if_statement and flag is False:
                temp, current_states = DFG_php(child, index_to_code, current_states)
                DFG += temp
            else:
                flag = True
                temp, new_states = DFG_php(child, index_to_code, states)
                DFG += temp
                others_states.append(new_states)
        others_states.append(current_states)
        new_states = {}
        for dic in others_states:
            for key in dic:
                if key not in new_states:
                    new_states[key] = dic[key].copy()
                else:
                    new_states[key] += dic[key]
        for key in states:
            if key not in new_states:
                new_states[key] = states[key]
            else:
                new_states[key] += states[key]
        for key in new_states:
            new_states[key] = sorted(list(set(new_states[key])))
        return sorted(DFG, key=lambda x: x[1]), new_states
    elif root_node.type in for_statement:
        DFG = []
        for child in root_node.children:
            temp, states = DFG_php(child, index_to_code, states)
            DFG += temp
        flag = False
        for child in root_node.children:
            if flag:
                temp, states = DFG_php(child, index_to_code, states)
                DFG += temp
            elif child.type == "assignment_expression":
                flag = True
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in enhanced_for_statement:
        name = None
        value = None
        for child in root_node.children:
            if child.type == "variable_name" and value is None:
                value = child
            elif child.type == "variable_name" and name is None:
                name = child
                break
        body = root_node.child_by_field_name("body")
        DFG = []
        for i in range(2):
            temp, states = DFG_php(value, index_to_code, states)
            DFG += temp
            name_indexs = tree_to_variable_index(name, index_to_code)
            value_indexs = tree_to_variable_index(value, index_to_code)
            for index1 in name_indexs:
                idx1, code1 = index_to_code[index1]
                for index2 in value_indexs:
                    idx2, code2 = index_to_code[index2]
                    DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
                states[code1] = [idx1]
            temp, states = DFG_php(body, index_to_code, states)
            DFG += temp
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in while_statement:
        DFG = []
        for i in range(2):
            for child in root_node.children:
                temp, states = DFG_php(child, index_to_code, states)
                DFG += temp
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    else:
        DFG = []
        for child in root_node.children:
            if child.type in do_first_statement:
                temp, states = DFG_php(child, index_to_code, states)
                DFG += temp
        for child in root_node.children:
            if child.type not in do_first_statement:
                temp, states = DFG_php(child, index_to_code, states)
                DFG += temp

        return sorted(DFG, key=lambda x: x[1]), states


def DFG_javascript(root_node, index_to_code, states):
    assignment = ["assignment_pattern", "augmented_assignment_expression"]
    def_statement = ["variable_declarator"]
    increment_statement = ["update_expression"]
    if_statement = ["if_statement", "else"]
    for_statement = ["for_statement"]
    while_statement = ["while_statement"]
    do_first_statement = []
    states = states.copy()
    if (
            len(root_node.children) == 0 or root_node.type in ["string_literal", "string", "character_literal"]
    ) and root_node.type != "comment":
        idx, code = index_to_code[(root_node.start_point, root_node.end_point)]
        if root_node.type == code:
            return [], states
        elif code in states:
            return [(code, idx, "comesFrom", [code], states[code].copy())], states
        else:
            if root_node.type == "identifier":
                states[code] = [idx]
            return [(code, idx, "comesFrom", [], [])], states
    elif root_node.type in def_statement:
        name = root_node.child_by_field_name("name")
        value = root_node.child_by_field_name("value")
        DFG = []
        if value is None:
            indexs = tree_to_variable_index(name, index_to_code)
            for index in indexs:
                idx, code = index_to_code[index]
                DFG.append((code, idx, "comesFrom", [], []))
                states[code] = [idx]
            return sorted(DFG, key=lambda x: x[1]), states
        else:
            name_indexs = tree_to_variable_index(name, index_to_code)
            value_indexs = tree_to_variable_index(value, index_to_code)
            temp, states = DFG_javascript(value, index_to_code, states)
            DFG += temp
            for index1 in name_indexs:
                idx1, code1 = index_to_code[index1]
                for index2 in value_indexs:
                    idx2, code2 = index_to_code[index2]
                    DFG.append((code1, idx1, "comesFrom", [code2], [idx2]))
                states[code1] = [idx1]
            return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in assignment:
        left_nodes = root_node.child_by_field_name("left")
        right_nodes = root_node.child_by_field_name("right")
        DFG = []
        temp, states = DFG_javascript(right_nodes, index_to_code, states)
        DFG += temp
        name_indexs = tree_to_variable_index(left_nodes, index_to_code)
        value_indexs = tree_to_variable_index(right_nodes, index_to_code)
        for index1 in name_indexs:
            idx1, code1 = index_to_code[index1]
            for index2 in value_indexs:
                idx2, code2 = index_to_code[index2]
                DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
            states[code1] = [idx1]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in increment_statement:
        DFG = []
        indexs = tree_to_variable_index(root_node, index_to_code)
        for index1 in indexs:
            idx1, code1 = index_to_code[index1]
            for index2 in indexs:
                idx2, code2 = index_to_code[index2]
                DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
            states[code1] = [idx1]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in if_statement:
        DFG = []
        current_states = states.copy()
        others_states = []
        flag = False
        tag = False
        if "else" in root_node.type:
            tag = True
        for child in root_node.children:
            if "else" in child.type:
                tag = True
            if child.type not in if_statement and flag is False:
                temp, current_states = DFG_javascript(child, index_to_code, current_states)
                DFG += temp
            else:
                flag = True
                temp, new_states = DFG_javascript(child, index_to_code, states)
                DFG += temp
                others_states.append(new_states)
        others_states.append(current_states)
        if tag is False:
            others_states.append(states)
        new_states = {}
        for dic in others_states:
            for key in dic:
                if key not in new_states:
                    new_states[key] = dic[key].copy()
                else:
                    new_states[key] += dic[key]
        for key in states:
            if key not in new_states:
                new_states[key] = states[key]
            else:
                new_states[key] += states[key]
        for key in new_states:
            new_states[key] = sorted(list(set(new_states[key])))
        return sorted(DFG, key=lambda x: x[1]), new_states
    elif root_node.type in for_statement:
        DFG = []
        for child in root_node.children:
            temp, states = DFG_javascript(child, index_to_code, states)
            DFG += temp
        flag = False
        for child in root_node.children:
            if flag:
                temp, states = DFG_javascript(child, index_to_code, states)
                DFG += temp
            elif child.type == "variable_declaration":
                flag = True
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in while_statement:
        DFG = []
        for i in range(2):
            for child in root_node.children:
                temp, states = DFG_javascript(child, index_to_code, states)
                DFG += temp
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    else:
        DFG = []
        for child in root_node.children:
            if child.type in do_first_statement:
                temp, states = DFG_javascript(child, index_to_code, states)
                DFG += temp
        for child in root_node.children:
            if child.type not in do_first_statement:
                temp, states = DFG_javascript(child, index_to_code, states)
                DFG += temp

        return sorted(DFG, key=lambda x: x[1]), states


def DFG_rust(root_node, index_to_code, states):
    assignment = ["assignment_expression", "compound_assignment_expr", "let_expression"]
    def_statement = ["function_item"]
    if_statement = ["if_expression", "if_let_expression", "match_expression", "else"]
    for_statement = ["for_expression"]
    enhanced_for_statement = ["for_each_statement"]
    while_statement = ["while_expression", "while_let_expression", "loop_expression"]
    do_first_statement = []
    states = states.copy()
    if (
            len(root_node.children) == 0 or root_node.type in ["string_literal", "string", "character_literal"]
    ) and root_node.type != "comment":
        idx, code = index_to_code[(root_node.start_point, root_node.end_point)]
        if root_node.type == code:
            return [], states
        elif code in states:
            return [(code, idx, "comesFrom", [code], states[code].copy())], states
        else:
            if root_node.type == "identifier":
                states[code] = [idx]
            return [(code, idx, "comesFrom", [], [])], states
    elif root_node.type in def_statement:
        if len(root_node.children) >= 3:
            name = root_node.children[1]
            value = root_node.children[2]
        else:
            name = root_node.children[1]
            value = None
        DFG = []
        if value is None:
            indexs = tree_to_variable_index(name, index_to_code)
            for index in indexs:
                idx, code = index_to_code[index]
                DFG.append((code, idx, "comesFrom", [], []))
                states[code] = [idx]
            return sorted(DFG, key=lambda x: x[1]), states
        else:
            name_indexs = tree_to_variable_index(name, index_to_code)
            value_indexs = tree_to_variable_index(value, index_to_code)
            temp, states = DFG_rust(value, index_to_code, states)
            DFG += temp
            for index1 in name_indexs:
                idx1, code1 = index_to_code[index1]
                for index2 in value_indexs:
                    idx2, code2 = index_to_code[index2]
                    DFG.append((code1, idx1, "comesFrom", [code2], [idx2]))
                states[code1] = [idx1]
            return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in assignment:
        left_nodes = root_node.child_by_field_name("left")
        right_nodes = root_node.child_by_field_name("right")
        DFG = []
        temp, states = DFG_rust(right_nodes, index_to_code, states)
        DFG += temp
        name_indexs = tree_to_variable_index(left_nodes, index_to_code)
        value_indexs = tree_to_variable_index(right_nodes, index_to_code)
        for index1 in name_indexs:
            idx1, code1 = index_to_code[index1]
            for index2 in value_indexs:
                idx2, code2 = index_to_code[index2]
                DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
            states[code1] = [idx1]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in if_statement:
        DFG = []
        current_states = states.copy()
        others_states = []
        flag = False
        tag = False
        if "else" in root_node.type:
            tag = True
        for child in root_node.children:
            if "else" in child.type:
                tag = True
            if child.type not in if_statement and flag is False:
                temp, current_states = DFG_rust(child, index_to_code, current_states)
                DFG += temp
            else:
                flag = True
                temp, new_states = DFG_rust(child, index_to_code, states)
                DFG += temp
                others_states.append(new_states)
        others_states.append(current_states)
        if tag is False:
            others_states.append(states)
        new_states = {}
        for dic in others_states:
            for key in dic:
                if key not in new_states:
                    new_states[key] = dic[key].copy()
                else:
                    new_states[key] += dic[key]
        for key in new_states:
            new_states[key] = sorted(list(set(new_states[key])))
        return sorted(DFG, key=lambda x: x[1]), new_states
    elif root_node.type in for_statement:
        DFG = []
        for child in root_node.children:
            temp, states = DFG_rust(child, index_to_code, states)
            DFG += temp
        flag = False
        for child in root_node.children:
            if flag:
                temp, states = DFG_rust(child, index_to_code, states)
                DFG += temp
            elif child.type == "local_variable_declaration":
                flag = True
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in enhanced_for_statement:
        name = root_node.child_by_field_name("left")
        value = root_node.child_by_field_name("right")
        body = root_node.child_by_field_name("body")
        DFG = []
        for i in range(2):
            temp, states = DFG_rust(value, index_to_code, states)
            DFG += temp
            name_indexs = tree_to_variable_index(name, index_to_code)
            value_indexs = tree_to_variable_index(value, index_to_code)
            for index1 in name_indexs:
                idx1, code1 = index_to_code[index1]
                for index2 in value_indexs:
                    idx2, code2 = index_to_code[index2]
                    DFG.append((code1, idx1, "computedFrom", [code2], [idx2]))
                states[code1] = [idx1]
            temp, states = DFG_rust(body, index_to_code, states)
            DFG += temp
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    elif root_node.type in while_statement:
        DFG = []
        for i in range(2):
            for child in root_node.children:
                temp, states = DFG_rust(child, index_to_code, states)
                DFG += temp
        dic = {}
        for x in DFG:
            if (x[0], x[1], x[2]) not in dic:
                dic[(x[0], x[1], x[2])] = [x[3], x[4]]
            else:
                dic[(x[0], x[1], x[2])][0] = list(set(dic[(x[0], x[1], x[2])][0] + x[3]))
                dic[(x[0], x[1], x[2])][1] = sorted(list(set(dic[(x[0], x[1], x[2])][1] + x[4])))
        DFG = [(x[0], x[1], x[2], y[0], y[1]) for x, y in sorted(dic.items(), key=lambda t: t[0][1])]
        return sorted(DFG, key=lambda x: x[1]), states
    else:
        DFG = []
        for child in root_node.children:
            if child.type in do_first_statement:
                temp, states = DFG_rust(child, index_to_code, states)
                DFG += temp
        for child in root_node.children:
            if child.type not in do_first_statement:
                temp, states = DFG_rust(child, index_to_code, states)
                DFG += temp

        return sorted(DFG, key=lambda x: x[1]), states


def DFG_prolog(root_node, index_to_code, states):
    states = states.copy()

    if len(root_node.children) == 0 or root_node.type in ["string_literal", "string", "character_literal", "atom",
                                                          "variable_term", "integer", "float_number"]:
        if root_node.type == "comment":
            return [], states
        idx, code = index_to_code[(root_node.start_point, root_node.end_point)]
        if root_node.type == code:
            return [], states
        elif code in states:
            return [(code, idx, "comesFrom", [code], states[code].copy())], states
        else:
            if root_node.type == "variable_term":
                states[code] = [idx]
            return [(code, idx, "comesFrom", [], [])], states

    if root_node.type == "clause_term":
        head_children = []
        body_children = []
        separator_found = False
        for child in root_node.children:
            if len(child.children) == 0:
                child_idx, child_code = index_to_code.get((child.start_point, child.end_point), (None, None))
                if child_code == ":-":
                    separator_found = True
                    continue
            if not separator_found:
                head_children.append(child)
            else:
                body_children.append(child)

        dfg_head = []
        states_head = states.copy()
        for child in head_children:
            temp, states_head = DFG_prolog(child, index_to_code, states_head)
            dfg_head += temp

        dfg_body = []
        states_body = states.copy()
        for child in body_children:
            temp, states_body = DFG_prolog(child, index_to_code, states_body)
            dfg_body += temp

        merged_states = {}
        for s in [states_head, states_body]:
            for key, val in s.items():
                if key in merged_states:
                    merged_states[key] = sorted(list(set(merged_states[key] + val)))
                else:
                    merged_states[key] = val.copy()

        head_var_indices = []
        for child in head_children:
            head_var_indices += tree_to_variable_index(child, index_to_code)
        body_var_indices = []
        for child in body_children:
            body_var_indices += tree_to_variable_index(child, index_to_code)
        head_vars = {}
        for index in head_var_indices:
            idx_token, code_token = index_to_code[index]
            head_vars.setdefault(code_token, []).append(index)
        body_vars = {}
        for index in body_var_indices:
            idx_token, code_token = index_to_code[index]
            body_vars.setdefault(code_token, []).append(index)
        computed_edges = []
        for var, head_indexes in head_vars.items():
            if var in body_vars:
                right_tokens = body_vars[var]
                body_token_positions = [index_to_code[x][1] for x in right_tokens]
                body_token_codes = [index_to_code[x][0] for x in right_tokens]
                for token_index in head_indexes:
                    idx_token, code_token = index_to_code[token_index]
                    computed_edges.append(
                        (code_token, idx_token, "computedFrom", body_token_positions, body_token_codes))
                    merged_states[code_token] = [idx_token]
        dfg = sorted(dfg_head + dfg_body + computed_edges, key=lambda x: x[1])
        return dfg, merged_states

    if root_node.type == "directive_term":
        head_children = []
        body_children = []
        separator_found = False
        for child in root_node.children:
            if len(child.children) == 0:
                child_idx, child_code = index_to_code.get((child.start_point, child.end_point), (None, None))
                if child_code == ":-":
                    separator_found = True
                    continue
            if not separator_found:
                head_children.append(child)
            else:
                body_children.append(child)
        dfg_head = []
        states_head = states.copy()
        for child in head_children:
            temp, states_head = DFG_prolog(child, index_to_code, states_head)
            dfg_head += temp
        dfg_body = []
        states_body = states.copy()
        for child in body_children:
            temp, states_body = DFG_prolog(child, index_to_code, states_body)
            dfg_body += temp
        merged_states = {}
        for s in [states_head, states_body]:
            for key, val in s.items():
                if key in merged_states:
                    merged_states[key] = sorted(list(set(merged_states[key] + val)))
                else:
                    merged_states[key] = val.copy()
        head_var_indices = []
        for child in head_children:
            head_var_indices += tree_to_variable_index(child, index_to_code)
        body_var_indices = []
        for child in body_children:
            body_var_indices += tree_to_variable_index(child, index_to_code)
        head_vars = {}
        for index in head_var_indices:
            idx_token, code_token = index_to_code[index]
            head_vars.setdefault(code_token, []).append(index)
        body_vars = {}
        for index in body_var_indices:
            idx_token, code_token = index_to_code[index]
            body_vars.setdefault(code_token, []).append(index)
        computed_edges = []
        for var, head_indexes in head_vars.items():
            if var in body_vars:
                right_tokens = body_vars[var]
                body_token_positions = [index_to_code[x][1] for x in right_tokens]
                body_token_codes = [index_to_code[x][0] for x in right_tokens]
                for token_index in head_indexes:
                    idx_token, code_token = index_to_code[token_index]
                    computed_edges.append(
                        (code_token, idx_token, "computedFrom", body_token_positions, body_token_codes))
                    merged_states[code_token] = [idx_token]
        dfg = sorted(dfg_head + dfg_body + computed_edges, key=lambda x: x[1])
        return dfg, merged_states

    dfg = []
    for child in root_node.children:
        temp, states = DFG_prolog(child, index_to_code, states)
        dfg += temp
    return sorted(dfg, key=lambda x: x[1]), states
