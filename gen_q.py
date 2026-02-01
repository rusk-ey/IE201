import random
import numpy

def basic_func():
    return random.randint(1,100)

class Problem:

    def __init__(
        self,


        type = None,
        type_list = None,
        n = None,
        i = None,
        PF = None,
        A = None,
        G = None,
        freq = None,
        P = None,
        flip = None,
        cash_flows = None,
        sol = None
    ):
        self.type = None #problem type
        self.type_list = None #list of valid problem types
        self.n = None #number of time periods (assumed to be years by default)
        self.i = None #yearly interest rate
        self.PF = None
        self.A = None #uniform series parameter (cash flow in every time period)
        self.G = None #gradient series parameter
        self.freq = None
        self.P = None #binary, decides whether present value or future value needs to be calculated
        self.flip = None
        self.cash_flows = None #dictionary containing cash flows in each time period
        self.sol = None

    def get_type(self, response_percentages):
        # If no response percentages are provided, treat all types equally
        if not response_percentages:
            self.type_list = ['Irregular', 'Uniform', 'Gradient']
            self.type = random.choice(self.type_list)
            return self.type

        # Calculate weights for each problem type (lower correctness → higher weight)
        self.type_list = ['Irregular', 'Uniform', 'Gradient']
        weights = []
        for t in self.type_list:
            # Invert correctness percentage: lower correctness → higher weight
            # Add small constant (e.g., 0.01) to avoid zero probabilities
            weight = 1.0 - response_percentages.get(t, 0.0) + 0.2
            weights.append(weight)
            print("WEIGHTS", weights)

        # Randomly select a type based on the calculated weights
        self.type = random.choices(self.type_list, weights=weights, k=1)[0]
        return self.type

    def get_problem(self):


        self.sol = 0
        P_or_F = random.randint(1,2)
        if P_or_F == 1:
            self.P = True
        else:
            self.P = True


        self.n = random.randint(5,10)
        self.i = random.randint(4,10) / 100

        self.cash_flows = {}
        for period in range(0, self.n + 1):
            self.cash_flows[period] = 0


        if self.type == 'Irregular':
            self.n = random.randint(4, 6)
            for period in range(1, self.n + 1):
                self.cash_flows[period] = random.randint(0, 10)*100
            for period in range(0, self.n + 1):
                if self.P:
                    self.sol += self.cash_flows[period]*((1+self.i)**(-period))
                else:
                    self.sol += self.cash_flows[period] * ((1 + self.i) ** (period))
        elif self.type == 'Uniform':
            self.A = random.randint(0, 10) * 100
            for period in range(1, self.n + 1):
                self.cash_flows[period] = self.A
            for period in range(1, self.n + 1):
                if self.P:
                    self.sol += self.cash_flows[period]*((1+self.i)**(-period))
                else:
                    self.sol += self.cash_flows[period] * ((1 + self.i) ** (period))

        elif self.type == 'Gradient':
            self.G = random.randint(1, 5) * 100
            self.cash_flows[0] = 0
            for period in range(1, self.n + 1):
                self.cash_flows[period] = (period - 1)*self.G
            for period in range(0, self.n + 1):
                if self.P:
                    self.sol += self.cash_flows[period]*((1+self.i)**(-period))
                else:
                    self.sol += self.cash_flows[period] * ((1 + self.i) ** (period))



print(basic_func())
problem = Problem()
print(problem.get_type([]))
print(problem.get_problem())
print("CF", problem.cash_flows, problem.n, problem.i, problem.P, problem.A, problem.G)
print("SOL", problem.sol)
