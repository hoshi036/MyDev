
#[((Pythonで) 書く (Lisp) インタプリタ)](http://www.aoky.net/articles/peter_norvig/lispy.htm)

################ Lispy: Scheme Interpreter in Python

## (c) Peter Norvig, 2010; See http://norvig.com/lispy.html


# 更新履歴
## 202311251821： eval()でif isa()がTrueのとき、環境内で変数名が見つからないときを例外処理して変数名をエラー表示で示すようにした。

################ Symbol、Procedure、Envクラス

from __future__ import division

Symbol = str

class AbstEnv(dict):
    "環境: ペア{'var':val}のdictで、外部環境(outer)を持つ。"
    def __init__(self, parms=(), args=()):
        self.update(zip(parms,args))

    def find(self, var):
        "var が現れる一番内側のEnvを見つける。"
        return self if var in self else self.outer.find(var)
    
class Env(AbstEnv):
    "環境: ペア{'var':val}のdictで、外部環境(outer)を持つ。"
    def __init__(self, parms=(), args=(), outer:AbstEnv=None):
        super().__init__(parms, args)
        self.outer = outer
        if (outer!=None): self.update(outer)

def add_globals(env):
    "環境にScheme標準の手続きをいくつか追加する"
    import math, operator as op
    env.update(vars(math)) # sin, sqrt, ...
    '''env.update(
    {'+':op.add, '-':op.sub, '*':op.mul, '/':op.div, 'not':op.not_,
        '>':op.gt, '<':op.lt, '>=':op.ge, '<=':op.le, '=':op.eq, 
        'equal?':op.eq, 'eq?':op.is_, 'length':len, 'cons':lambda x,y:[x]+y,
        'car':lambda x:x[0],'cdr':lambda x:x[1:], 'append':op.add,  
        'list':lambda *x:list(x), 'list?': lambda x:isa(x,list), 
    'null?':lambda x:x==[], 'symbol?':lambda x: isa(x, Symbol)})
    '''
    # op.subとop.divを除いた。
    # Numpy.ndarrayに対応させる -> Numpy.ndarrayに対応していることが分かった。
    env.update(
    {'+':op.add, '*':op.mul, '@':op.matmul, '**':op.pow, 'not':op.not_,
    '>':op.gt, '<':op.lt, '>=':op.ge, '<=':op.le, '=':op.eq, 
    'equal?':op.eq, 'eq?':op.is_, 'length':len, 'cons':lambda x,y:[x]+y,
    'car':lambda x:x[0],'cdr':lambda x:x[1:], 'append':op.add,  
    'list':lambda *x:list(x), 'list?': lambda x:isa(x,list), 
    'null?':lambda x:x==[], 'symbol?':lambda x: isa(x, Symbol)})
    return env

global_env = add_globals(Env())  # 出来れば、Interpretの呼び出し側で指定し、この「global_env」は使わない。∵グローバル変数を使いたくない。

isa = isinstance

################ eval

class LispInterpreter():
#    isa = isinstance
    def __init__(self, env=global_env, debug=False):
        self.parse = self.read
        self.debug = debug
        self.env = env
#        self.global_env = add_globals(Env())
        
    def eval(self, x, env=None):
        "環境の中で式を評価する。"
        if(env==None): env = self.env
        if isa(x, Symbol):             # 変数参照
            try:
                return env.find(x)[x]
            except:
                print(f'{x} is not found in environment')
        elif not isa(x, list):         # 定数リテラル
            return x                
        elif x[0] == 'quote':          # (quote exp)
            (_, exp) = x
            return exp
        elif x[0] == 'if':             # (if test conseq alt)
            (_, test, conseq, alt) = x
            return self.eval((conseq if self.eval(test, env) else alt), env)
        elif x[0] == 'set!':           # (set! var exp)
            (_, var, exp) = x
            env.find(var)[var] = self.eval(exp, env)
        elif x[0] == 'define':         # (define var exp)
            (_, var, exp) = x
            env[var] = self.eval(exp, env)
        elif x[0] == 'lambda':         # (lambda (var*) exp)
            (_, vars, exp) = x
            return lambda *args: self.eval(exp, Env(vars, args, env))
        elif x[0] == 'begin':          # (begin exp*)
            for exp in x[1:]:
                val = self.eval(exp, env)
            return val
        else:                          # (proc exp*)
            exps = [self.eval(exp, env) for exp in x]
            proc = exps.pop(0)
            return proc(*exps)

    ################ parse、read、ユーザ対話

    def read(self, s):
        "文字列からScheme式を読み込む。"
        return self.read_from(self.tokenize(s))

    #parse = read #included in __init__()

    def tokenize(self, s):
        "文字列をトークンのリストに変換する。"
        output = s.replace('(',' ( ').replace(')',' ) ').split()
        if(self.debug):print(f'output = {output}')
        return output

    def read_from(self, tokens):
        "トークンの列から式を読み込む。"
        if len(tokens) == 0:
            raise SyntaxError('unexpected EOF while reading')
        token = tokens.pop(0)
        if '(' == token:
            L = []
            while tokens[0] != ')':
                L.append(self.read_from(tokens))
            tokens.pop(0) # pop off ')'
            if(self.debug):print(f'L={L}')
            return L
        elif ')' == token:
            raise SyntaxError('unexpected )')
        else:
            return self.atom(token)

    def atom(self, token):
        "数は数にし、それ以外のトークンはシンボルにする。"
        try: return int(token)
        except ValueError:
            try: return float(token)
            except ValueError:
                return Symbol(token)

    def to_string(self, exp):
        "PythonオブジェクトをLispの読める文字列に戻す。"
        return '('+' '.join(map(self.to_string, exp))+')' if isa(exp, list) else str(exp)

    def repl(self, prompt='lis.py> '):
        "read-eval-print-loopのプロンプト"
        while True:
            val = self.eval(self.parse(input(prompt)))
            if val is not None: print(self.to_string(val))
            
    #########################追加
    def interpret(self, expr):
        val = self.eval(self.parse(expr))
        if val is not None: print(self.to_string(val))
        return val