#!/usr/bin/env python3
"""
Strategy Optimization Module

Optimizes trading strategy parameters using various optimization techniques
including grid search, random search, and evolutionary algorithms.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from sklearn.model_selection import ParameterGrid
import scipy.optimize as opt

from ..core.backtesting_engine import BacktestingEngine, BacktestConfig, BacktestResult
from ..strategies.base_strategy import BaseWeatherStrategy

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result of parameter optimization"""
    best_parameters: Dict[str, Any]
    best_score: float
    optimization_history: List[Dict[str, Any]]
    convergence_info: Dict[str, Any]
    optimization_method: str


@dataclass
class ParameterSpace:
    """Definition of parameter search space"""
    name: str
    param_type: str  # 'continuous', 'discrete', 'categorical'
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    values: Optional[List[Any]] = None
    distribution: str = 'uniform'  # 'uniform', 'log', 'normal'


class StrategyOptimizer:
    """
    Optimizes trading strategy parameters for maximum performance

    Supports multiple optimization methods:
    - Grid Search: Exhaustive search over parameter combinations
    - Random Search: Random sampling from parameter space
    - Bayesian Optimization: Gaussian process-based optimization
    - Evolutionary Algorithms: Genetic algorithm-based optimization
    """

    def __init__(self,
                 backtest_engine: BacktestingEngine,
                 optimization_target: str = 'sharpe_ratio'):
        """
        Initialize optimizer

        Args:
            backtest_engine: BacktestingEngine instance
            optimization_target: Metric to optimize ('sharpe_ratio', 'total_return', 'win_rate', etc.)
        """
        self.engine = backtest_engine
        self.optimization_target = optimization_target
        self.logger = logging.getLogger(__name__)

    def optimize_strategy(self,
                         strategy_class: type,
                         parameter_spaces: Dict[str, ParameterSpace],
                         optimization_method: str = 'grid_search',
                         max_evaluations: int = 50,
                         n_jobs: int = 1) -> OptimizationResult:
        """
        Optimize strategy parameters

        Args:
            strategy_class: Strategy class to optimize
            parameter_spaces: Dictionary of parameter spaces to search
            optimization_method: Optimization method to use
            max_evaluations: Maximum number of parameter evaluations
            n_jobs: Number of parallel jobs

        Returns:
            OptimizationResult with best parameters and optimization history
        """
        self.logger.info(f"Starting optimization of {strategy_class.__name__} using {optimization_method}")

        if optimization_method == 'grid_search':
            return self._grid_search_optimization(strategy_class, parameter_spaces, max_evaluations, n_jobs)
        elif optimization_method == 'random_search':
            return self._random_search_optimization(strategy_class, parameter_spaces, max_evaluations, n_jobs)
        elif optimization_method == 'bayesian':
            return self._bayesian_optimization(strategy_class, parameter_spaces, max_evaluations)
        elif optimization_method == 'evolutionary':
            return self._evolutionary_optimization(strategy_class, parameter_spaces, max_evaluations)
        else:
            raise ValueError(f"Unknown optimization method: {optimization_method}")

    def _grid_search_optimization(self,
                                 strategy_class: type,
                                 parameter_spaces: Dict[str, ParameterSpace],
                                 max_evaluations: int,
                                 n_jobs: int) -> OptimizationResult:
        """Perform grid search optimization"""
        # Create parameter grid
        param_grid = {}
        for param_name, param_space in parameter_spaces.items():
            if param_space.param_type == 'discrete':
                param_grid[param_name] = range(int(param_space.min_value), int(param_space.max_value) + 1)
            elif param_space.param_type == 'categorical':
                param_grid[param_name] = param_space.values
            else:
                # For continuous parameters, create a discrete grid
                n_points = min(10, max_evaluations // 10)  # Limit grid size
                if param_space.distribution == 'log':
                    param_grid[param_name] = np.logspace(
                        np.log10(param_space.min_value),
                        np.log10(param_space.max_value),
                        n_points
                    )
                else:
                    param_grid[param_name] = np.linspace(
                        param_space.min_value,
                        param_space.max_value,
                        n_points
                    )

        grid = ParameterGrid(param_grid)
        total_combinations = len(grid)

        self.logger.info(f"Grid search with {total_combinations} parameter combinations")

        # Evaluate parameter combinations
        results = self._evaluate_parameter_combinations(
            strategy_class, list(grid)[:max_evaluations], n_jobs
        )

        # Find best result
        best_result = max(results, key=lambda x: x['score'])
        best_params = best_result['parameters']

        return OptimizationResult(
            best_parameters=best_params,
            best_score=best_result['score'],
            optimization_history=results,
            convergence_info={'total_evaluations': len(results), 'method': 'grid_search'},
            optimization_method='grid_search'
        )

    def _random_search_optimization(self,
                                   strategy_class: type,
                                   parameter_spaces: Dict[str, ParameterSpace],
                                   max_evaluations: int,
                                   n_jobs: int) -> OptimizationResult:
        """Perform random search optimization"""
        self.logger.info(f"Random search with {max_evaluations} evaluations")

        # Generate random parameter combinations
        param_combinations = []
        for _ in range(max_evaluations):
            params = {}
            for param_name, param_space in parameter_spaces.items():
                if param_space.param_type == 'continuous':
                    if param_space.distribution == 'log':
                        params[param_name] = np.random.uniform(
                            np.log10(param_space.min_value),
                            np.log10(param_space.max_value)
                        )
                        params[param_name] = 10 ** params[param_name]
                    elif param_space.distribution == 'normal':
                        mean = (param_space.min_value + param_space.max_value) / 2
                        std = (param_space.max_value - param_space.min_value) / 6
                        params[param_name] = np.random.normal(mean, std)
                        params[param_name] = np.clip(params[param_name],
                                                   param_space.min_value,
                                                   param_space.max_value)
                    else:  # uniform
                        params[param_name] = np.random.uniform(
                            param_space.min_value, param_space.max_value
                        )
                elif param_space.param_type == 'discrete':
                    params[param_name] = np.random.randint(
                        param_space.min_value, param_space.max_value + 1
                    )
                elif param_space.param_type == 'categorical':
                    params[param_name] = np.random.choice(param_space.values)

            param_combinations.append(params)

        # Evaluate parameter combinations
        results = self._evaluate_parameter_combinations(
            strategy_class, param_combinations, n_jobs
        )

        # Find best result
        best_result = max(results, key=lambda x: x['score'])
        best_params = best_result['parameters']

        return OptimizationResult(
            best_parameters=best_params,
            best_score=best_result['score'],
            optimization_history=results,
            convergence_info={'total_evaluations': len(results), 'method': 'random_search'},
            optimization_method='random_search'
        )

    def _bayesian_optimization(self,
                              strategy_class: type,
                              parameter_spaces: Dict[str, ParameterSpace],
                              max_evaluations: int) -> OptimizationResult:
        """Perform Bayesian optimization"""
        # This is a simplified implementation
        # In practice, you would use libraries like scikit-optimize or GPyOpt

        self.logger.info(f"Bayesian optimization with {max_evaluations} evaluations")

        # For now, fall back to random search with some intelligence
        # A full Bayesian optimization would require additional dependencies

        return self._random_search_optimization(
            strategy_class, parameter_spaces, max_evaluations, 1
        )

    def _evolutionary_optimization(self,
                                  strategy_class: type,
                                  parameter_spaces: Dict[str, ParameterSpace],
                                  max_evaluations: int) -> OptimizationResult:
        """Perform evolutionary optimization"""
        # Simplified genetic algorithm implementation

        self.logger.info(f"Evolutionary optimization with {max_evaluations} evaluations")

        population_size = min(20, max_evaluations // 2)
        n_generations = max_evaluations // population_size

        # Initialize population
        population = self._initialize_population(parameter_spaces, population_size)

        best_fitness = float('-inf')
        best_individual = None
        optimization_history = []

        for generation in range(n_generations):
            # Evaluate fitness
            fitness_scores = []
            for individual in population:
                result = self._evaluate_single_parameter_set(strategy_class, individual)
                fitness = result['score']
                fitness_scores.append(fitness)

                optimization_history.append({
                    'generation': generation,
                    'parameters': individual,
                    'score': fitness,
                    'timestamp': datetime.now()
                })

                if fitness > best_fitness:
                    best_fitness = fitness
                    best_individual = individual.copy()

            # Create next generation
            if generation < n_generations - 1:
                population = self._evolve_population(population, fitness_scores, parameter_spaces)

        return OptimizationResult(
            best_parameters=best_individual,
            best_score=best_fitness,
            optimization_history=optimization_history,
            convergence_info={
                'generations': n_generations,
                'population_size': population_size,
                'method': 'evolutionary'
            },
            optimization_method='evolutionary'
        )

    def _initialize_population(self,
                              parameter_spaces: Dict[str, ParameterSpace],
                              population_size: int) -> List[Dict[str, Any]]:
        """Initialize population for evolutionary algorithm"""
        population = []

        for _ in range(population_size):
            individual = {}
            for param_name, param_space in parameter_spaces.items():
                if param_space.param_type == 'continuous':
                    individual[param_name] = np.random.uniform(
                        param_space.min_value, param_space.max_value
                    )
                elif param_space.param_type == 'discrete':
                    individual[param_name] = np.random.randint(
                        param_space.min_value, param_space.max_value + 1
                    )
                elif param_space.param_type == 'categorical':
                    individual[param_name] = np.random.choice(param_space.values)

            population.append(individual)

        return population

    def _evolve_population(self,
                          population: List[Dict[str, Any]],
                          fitness_scores: List[float],
                          parameter_spaces: Dict[str, ParameterSpace]) -> List[Dict[str, Any]]:
        """Evolve population using selection, crossover, and mutation"""
        # Simple tournament selection and crossover
        new_population = []
        population_size = len(population)

        # Keep best individual (elitism)
        best_idx = np.argmax(fitness_scores)
        new_population.append(population[best_idx].copy())

        while len(new_population) < population_size:
            # Select parents
            parent1 = self._tournament_selection(population, fitness_scores)
            parent2 = self._tournament_selection(population, fitness_scores)

            # Crossover
            child = self._crossover(parent1, parent2, parameter_spaces)

            # Mutation
            child = self._mutate(child, parameter_spaces, mutation_rate=0.1)

            new_population.append(child)

        return new_population

    def _tournament_selection(self,
                             population: List[Dict[str, Any]],
                             fitness_scores: List[float]) -> Dict[str, Any]:
        """Tournament selection"""
        tournament_size = 3
        tournament_indices = np.random.choice(len(population), tournament_size, replace=False)
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_idx = tournament_indices[np.argmax(tournament_fitness)]
        return population[winner_idx].copy()

    def _crossover(self,
                  parent1: Dict[str, Any],
                  parent2: Dict[str, Any],
                  parameter_spaces: Dict[str, ParameterSpace]) -> Dict[str, Any]:
        """Single point crossover"""
        child = {}

        for param_name in parent1.keys():
            if np.random.random() < 0.5:
                child[param_name] = parent1[param_name]
            else:
                child[param_name] = parent2[param_name]

        return child

    def _mutate(self,
               individual: Dict[str, Any],
               parameter_spaces: Dict[str, ParameterSpace],
               mutation_rate: float) -> Dict[str, Any]:
        """Mutation operator"""
        mutated = individual.copy()

        for param_name, param_space in parameter_spaces.items():
            if np.random.random() < mutation_rate:
                if param_space.param_type == 'continuous':
                    # Add Gaussian noise
                    noise = np.random.normal(0, (param_space.max_value - param_space.min_value) * 0.1)
                    mutated[param_name] = np.clip(
                        individual[param_name] + noise,
                        param_space.min_value,
                        param_space.max_value
                    )
                elif param_space.param_type == 'discrete':
                    # Random new value
                    mutated[param_name] = np.random.randint(
                        param_space.min_value, param_space.max_value + 1
                    )
                elif param_space.param_type == 'categorical':
                    # Random new category
                    mutated[param_name] = np.random.choice(param_space.values)

        return mutated

    def _evaluate_parameter_combinations(self,
                                        strategy_class: type,
                                        param_combinations: List[Dict[str, Any]],
                                        n_jobs: int) -> List[Dict[str, Any]]:
        """Evaluate multiple parameter combinations"""
        results = []

        if n_jobs == 1:
            # Sequential evaluation
            for params in param_combinations:
                result = self._evaluate_single_parameter_set(strategy_class, params)
                results.append(result)
        else:
            # Parallel evaluation
            with ThreadPoolExecutor(max_workers=n_jobs) as executor:
                futures = [
                    executor.submit(self._evaluate_single_parameter_set, strategy_class, params)
                    for params in param_combinations
                ]

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Parameter evaluation failed: {e}")

        return results

    def _evaluate_single_parameter_set(self,
                                      strategy_class: type,
                                      parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single parameter set"""
        try:
            # Create strategy instance with parameters
            strategy = strategy_class(parameters=parameters)

            # Run backtest
            result = self.engine.run_backtest(strategy)

            # Extract optimization target
            score = self._extract_optimization_score(result)

            return {
                'parameters': parameters,
                'score': score,
                'result': result,
                'timestamp': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Failed to evaluate parameters {parameters}: {e}")
            return {
                'parameters': parameters,
                'score': float('-inf'),
                'error': str(e),
                'timestamp': datetime.now()
            }

    def _extract_optimization_score(self, result: BacktestResult) -> float:
        """Extract the optimization target score from backtest result"""
        if self.optimization_target == 'sharpe_ratio':
            return result.sharpe_ratio
        elif self.optimization_target == 'total_return':
            return result.total_return
        elif self.optimization_target == 'win_rate':
            return result.win_rate
        elif self.optimization_target == 'profit_factor':
            return result.metrics.get('profit_factor', 0)
        elif self.optimization_target == 'calmar_ratio':
            return result.metrics.get('calmar_ratio', 0)
        else:
            # Default to Sharpe ratio
            return result.sharpe_ratio

    def walk_forward_optimization(self,
                                 strategy_class: type,
                                 parameter_spaces: Dict[str, ParameterSpace],
                                 window_size: int = 30,
                                 step_size: int = 7) -> List[OptimizationResult]:
        """
        Perform walk-forward optimization

        Args:
            strategy_class: Strategy class to optimize
            parameter_spaces: Parameter spaces to search
            window_size: Size of optimization window in days
            step_size: Step size for moving window in days

        Returns:
            List of optimization results for each window
        """
        # This would require modifying the backtest engine to support date ranges
        # For now, return a placeholder implementation

        self.logger.info("Walk-forward optimization not yet implemented")
        return []