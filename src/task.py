from typing import Callable, Any
from pathlib import Path
import importlib.util

from src.utils import read_env


INTERNAL_TASKS = {
    'dcm2other': './src/algorithms/dcm2other.py'
}


class TaskDispatcher():
    def __init__(self):
        self.tasks: dict[str, Callable[..., Any]] = {}
        
    def register_tasks(self):
        print("importing internal tasks")
        for task, path in INTERNAL_TASKS.items():
            module_name, module = self.import_method(task, Path(path))
            self.tasks[task] = getattr(module, module_name)
            print(f"imported internal {task} function")
            
        print("importing external tasks")
        task_paths = read_env("algorithms")
        for task, paths in task_paths.items():
                        
            if not all([paths.values()]):
                print(f"external task '{task}' missing executable/script path")
                continue
                        
            exec_path = Path(paths['exec_path']).expanduser() 
            script_path = Path(paths['script_path']).expanduser()
            func_path = Path(paths['func_path'])
            
            if not exec_path.is_file():
                print(f"external task '{task}' executable path not found/not file '{exec_path}'")
                continue
            
            if not script_path.is_file():
                print(f"external task '{task}' script path not found/not file '{script_path}'")
                continue
                                      
            module_name, module = self.import_method(task, func_path)
            
            self.tasks[task] = getattr(module, module_name)
            print(f"registered external {task} function")
        print(f"registered tasks: {", ".join(self.tasks.keys())}")
    
    def import_method(self, task: str, func_path: Path):
        module_name = func_path.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name, func_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except RuntimeError as err:
            print(err)
            return None, None
        return module_name, module

    def get_task(self, task_name: str) -> Callable[..., Any]:
        try:
            if task_name not in self.tasks:
                raise KeyError(f"external task {task_name} not registered")
            return self.tasks[task_name]
        except KeyError as e:
            print(e)
        
        