# Инициализируем память значениями вектора
LOAD_CONST 10     # Значение 10
WRITE_MEM 0       # Память[0] = 10

LOAD_CONST -5     # Значение -5
WRITE_MEM 1       # Память[1] = -5

LOAD_CONST 0      # Значение 0
WRITE_MEM 2       # Память[2] = 0

LOAD_CONST 7      # Значение 7
WRITE_MEM 3       # Память[3] = 7

# Выполняем поэлементно операцию sgn()
LOAD_CONST 0      # Адрес 0
UNARY_SGN         # accumulator = sgn(Память[0])
WRITE_MEM 0       # Память[0] = accumulator

LOAD_CONST 1      # Адрес 1
UNARY_SGN         # accumulator = sgn(Память[1])
WRITE_MEM 1       # Память[1] = accumulator

LOAD_CONST 2      # Адрес 2
UNARY_SGN         # accumulator = sgn(Память[2])
WRITE_MEM 2       # Память[2] = accumulator

LOAD_CONST 3      # Адрес 3
UNARY_SGN         # accumulator = sgn(Память[3])
WRITE_MEM 3       # Память[3] = accumulator
