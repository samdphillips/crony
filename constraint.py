
import random

r = random.Random(1277)

unbound = object()


def debug(s, *v):
    print 'DEBUG:', s % v


class Var(object):
    def __init__(self, name, domain):
        # XXX: priority?
        self.name   = name
        self.domain = domain
        self.value  = unbound

    def is_unbound(self):
        return self.value is unbound

    def assign(self):
        self.value = self.domain.first()
        debug('setting %s to %s', self.name, self.value)

    def step(self):
        self.domain.hide(self.value)
        self.assign()

    def reset(self):
        self.domain.reset()

    def __repr__(self):
        return '<Var %s : %s>' % (self.name, self.value)


class ListDomain(object):
    def __init__(self, values):
        self._values = list(values)
        self._orig   = list(values)
        self._stack  = []
        self.reset()

    @property
    def values(self):
        return list(_values)

    def __len__(self):
        return len(self._values)

    def first(self):
        return self._values[0]

    def hide(self, v):
        self._values.remove(v)

    def reset(self):
        self._values = list(self._orig)
        r.shuffle(self._values)


class FuncConstraint(object):
    def __init__(self, vars, func):
        self.vars = vars
        self.func = func

    def check(self):
        debug('checking %s', self)
        return self.func(*[v.value for v in self.vars])

    def __repr__(self):
        vs = [str(v) for v in self.vars]
        vs = ', '.join(vs)
        return '%s(%s)' % (self.func.__name__, vs)


class Problem(object):
    def __init__(self):
        self.vars        = []
        self.constraints = []

    def add_var(self, name, domain):
        # XXX: check for dups
        # XXX: priority?
        v = Var(name, ListDomain(domain))
        self.vars.append(v)
        return v

    def add_constraint(self, constraint):
        self.constraints.append(constraint)

    def constraint(self, *vars):
        def wrapper(f):
            c = FuncConstraint(vars, f)
            self.add_constraint(c)
            return c
        return wrapper


class BacktrackSolver(object):
    def __init__(self, problem):
        self.problem = problem

    @property
    def vars(self):
        return self.problem.vars

    @property
    def constraints(self):
        return self.problem.constraints

    def step_vars(self):
        is_init = False
        for v in self.vars:
            if v.is_unbound():
                v.assign()
                is_init = True
        if is_init:
            return

        for v in self.vars:
            if len(v.domain) == 1:
                v.reset()
            else:
                v.step()
                return
        raise NoMoreSolutions(self.problem)

    def check_constraints(self):
        for c in self.constraints:
            if not c.check():
                return False
        return True

    def make_solution(self):
        d = {}
        for v in self.vars:
            d[v] = v.value
        return d

    def step(self):
        self.step_vars()
        if self.check_constraints():
            return self.make_solution()
        return None

    def solve(self):
        solution = None
        while solution is None:
            solution = self.step()
        return solution


#   S E N D
#   M O R E
# M O N E Y

puzzle = Problem()

D = puzzle.add_var('D', range(10))
E = puzzle.add_var('E', range(10))
Y = puzzle.add_var('Y', range(10))

N = puzzle.add_var('N', range(10))
R = puzzle.add_var('R', range(10))

O = puzzle.add_var('O', range(10))

S = puzzle.add_var('S', range(1,10))
M = puzzle.add_var('M', range(1,10))

@puzzle.constraint(E, N, D, O, R, Y, S, M)
def all_different(*vals):
    seen = set()
    for v in vals:
        if v in seen:
            return False
        else:
            seen.add(v)
    return True

@puzzle.constraint(E, N, D, O, R, Y, S, M)
def send_more_money(E, N, D, O, R, Y, S, M):
    send = S * 1000 + E * 100 + N * 10 + D
    more = M * 1000 + O * 100 + R * 10 + E
    money = M * 10000 + O * 1000 + N * 100 + E * 10 + Y
    return send + more == money



solver = BacktrackSolver(puzzle)
print solver.solve()
# for solution in solver:
#     print solution

