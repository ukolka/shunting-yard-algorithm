import string

class RPNOutput(object):
    """Output queue for infix to RPN conversion."""

    def __init__(self):
        self.__content = []

    def add(self, val):
        self.__content.append(val)

    def __repr__(self):
        return ''.join(map(str, self.__content))

    __str__ = __repr__

class Operator(object):
    """Represents mathematical operator."""
    LEFT = 0
    RIGHT = 1
    VALUES = "!^*/%+-="
    PROPS = {
        VALUES[0]: (5, RIGHT), # !
        VALUES[1]: (4, RIGHT), # ^
        VALUES[2]: (3, LEFT),  # *
        VALUES[3]: (3, LEFT),  # /
        VALUES[4]: (3, LEFT),  # %
        VALUES[5]: (2, LEFT),  # +
        VALUES[6]: (2, LEFT),  # -
        VALUES[7]: (1, RIGHT)  # =
    }
    def __init__(self, val):
        pos = self.VALUES.find(val)
        assert pos > -1
        self.__val = val
        self.__precedence = self.PROPS[self.VALUES[pos]][0]
        self.__associativity = self.PROPS[self.VALUES[pos]][1]

    def is_left_associative(self):
        return  self.__associativity == self.LEFT

    def is_right_associative(self):
        return self.__associativity == self.RIGHT


    def __lt__(self, other):
        return self.__precedence < other.__precedence

    def __le__(self, other):
        return self.__precedence <= other.__precedence

    def __repr__(self):
        return self.__val

    __str__ = __repr__


class OperatorStack(object):
    """Wraps operator stack."""
    def __init__(self):
        self.__stack = []

    def push(self, val):
        self.__stack.append(val)

    def top(self):
        """Peeks at the last element in the stack."""
        if len(self.__stack) > 0:
            return self.__stack[-1]
        return Token(Token.SOL, '', -1)

    def pop(self):
        return self.__stack.pop()

    def __str__(self):
        return ''.join(map(str, self.__stack))

class Token(object):
    """Represents type of a character."""
    SOL     = -1 # start of line
    EOL     = 0 # end of line
    IDENT   = 1 # identifier (variable or number)
    OP      = 2 # operator
    FUNC    = 3 # function
    ARG_SEP = 4 # argument separator
    L_PAREN = 5 # left parenthesis
    R_PAREN = 6 # right parenthesis

    REPR = { EOL: "EOL", IDENT: "IDEN", OP: "OP", FUNC: "FUNC", ARG_SEP: "ARG_SEP",
             L_PAREN: "L_PAREN", R_PAREN: "R_PAREN"}

    def __init__(self, type, val, pos):
        self.__type = type
        self.__val = val
        self.__pos = pos

    def type(self):
        return self.__type

    def val(self):
        return self.__val

    def pos(self):
        return self.__pos

    def __repr__(self):
        return str(self.val())

    __str__ = __repr__

class Tokenize(object):
    """Provides traversal with tokens."""

    def __init__(self, src):
        """Creates generator that is accessible with __next_token
        and keeps current token in __current_token"""

        self.__src = src
        self.__next_token = self.tokenize()
        self.__current_token = Token(Token.EOL, '', -1)

    def tokenize(self):
        """Makes a Token for each character in the source."""

        i = 0
        while i < len(self.__src):
            char = self.__src[i]
            if char in string.lowercase + string.digits:
                type = Token.IDENT
                val = char
            elif char in string.uppercase:
                type = Token.FUNC
                val = char
            elif char in Operator.VALUES:
                type = Token.OP
                val = Operator(char)
            elif char == "(":
                type = Token.L_PAREN
                val = char
            elif char == ")":
                type = Token.R_PAREN
                val = char
            elif char == ",":
                type = Token.ARG_SEP
                val = char
            else:
                # skip not described characters
                i += 1
                continue
            self.__current_token = Token(type, val, i)
            yield self.__current_token
            i += 1

    def next(self):
        """Get next Token from generator.
        If there are no more tokens - returns EOL"""
        for t in self.__next_token:
            return t
        self.__current_token = Token(Token.EOL, '   ', -1)
        return self.__current_token

    def token(self):
        return self.__current_token

    current = token

    def __str__(self):
        return "Tokenize(current_token: (type: {}, val: \"{}\", pos: {}))".format(
            Token.REPR[self.token().type()], self.token().val(), self.token().pos())

def shunting_yard(expression):
    operator_stack = OperatorStack()
    output_queue = RPNOutput()
    tokenized = Tokenize(expression)
    # Read the token.
    tokenized.next()
    while tokenized.current().type() != Token.EOL:
        # If the token is a number, then add it to the output queue.
        if tokenized.current().type() == Token.IDENT:
            output_queue.add(tokenized.token())
        # If the token is a function token, then push it onto the stack.
        elif tokenized.current().type() == Token.FUNC:
            operator_stack.push(tokenized.token())
        # If the token is a function argument separator (e.g., a comma):
        elif tokenized.current().type() == Token.ARG_SEP:
            # Until the token at the top of the stack is a left parenthesis,
            # pop operators off the stack onto the output queue.
            # If no left parentheses are encountered, either the separator
            # was misplaced or parentheses were mismatched.
            while operator_stack.top().type() not in (Token.L_PAREN, Token.SOL):
                output_queue.add(operator_stack.pop())
            assert operator_stack.top().type() == Token.L_PAREN, "Error: separator or parentheses mismatched"
        # If the token is an operator, o1, then:
        elif tokenized.current().type() == Token.OP:
            # while there is an operator token, o2, at the top of the stack, and
            # either o1 is left-associative and its precedence is less than or equal to that of o2,
            # or o1 has precedence less than that of o2,
            while operator_stack.top().type() == Token.OP and \
                  ((tokenized.current().val().is_left_associative()
                    and tokenized.current().val() <= operator_stack.top().val()) or \
                  tokenized.current().val() < operator_stack.top().val()):
                    # pop o2 off the stack, onto the output queue;
                    output_queue.add(operator_stack.pop())
            # push o1 onto the stack.
            operator_stack.push(tokenized.token())
        # If the token is a left parenthesis, then push it onto the stack.
        elif tokenized.current().type() == Token.L_PAREN:
            operator_stack.push(tokenized.token())
        # If the token is a right parenthesis
        elif tokenized.current().type() == Token.R_PAREN:
            # Until the token at the top of the stack is a left parenthesis,
            # pop operators off the stack onto the output queue.
            while operator_stack.top().type() != Token.L_PAREN:
                # Pop the left parenthesis from the stack, but not onto the output queue.
                output_queue.add(operator_stack.pop())
            # If the stack runs out without finding a left parenthesis, then there are mismatched parentheses.
            assert operator_stack.top().type() == Token.L_PAREN, "Error: parentheses mismatched"
            operator_stack.pop()
            # If the token at the top of the stack is a function token, pop it onto the output queue.
            if operator_stack.top().type() == Token.FUNC:
                output_queue.add(operator_stack.pop())

        tokenized.next()

    # When there are no more tokens to read
    # While there are still operator tokens in the stack:
    while operator_stack.top().type() in (Token.OP, Token.L_PAREN, Token.R_PAREN):
        # If the operator token on the top of the stack is a parenthesis, then there are mismatched parentheses.
        assert operator_stack.top().type() not in (Token.L_PAREN, Token.R_PAREN), "Error: parentheses mismatched"
        # Pop the operator onto the output queue.
        output_queue.add(operator_stack.pop())

    return str(output_queue)

def main(name, *args):
    exps = ("3 + 4 * 2 / ( 1 - 5 ) ^ 2 ^ 3", "a = D(f - b * c + d, !e, g)")
    for exp in exps:
        print exp, '\t', shunting_yard(exp)

if __name__ == '__main__':
    import sys
    main(*sys.argv)